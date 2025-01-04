import pytest
from unittest.mock import mock_open, patch, MagicMock
from backend.model import Post
from freezegun import freeze_time
import os
import time
import feedparser

@pytest.fixture
def set_timezone(request):
    original_tz = os.environ.get('TZ')
    tz = request.param
    os.environ['TZ'] = tz
    time.tzset()
    yield
    if original_tz is not None:
        os.environ['TZ'] = original_tz
    else:
        del os.environ['TZ']
    time.tzset()

@pytest.fixture
def mock_config(mock_config_base):
    mock_config_base.action_custom_config = {
        "BotRssFwd": {
            "enabled": True,
            "rsshub_url": "https://rsshub.example.com",
            "tasks": [
                {
                    "endpoint": "/test",
                    "enabled": True,
                    "new_topic": True,
                    "category_id": 100
                }
            ]
        }
    }
    return mock_config_base

@pytest.fixture
def mock_rss_feed():
    with open(os.path.join(os.path.dirname(__file__), "../../data/rss_feed_data.xml"), "r") as f:
        feeds = feedparser.parse(f.read())
    with patch("feedparser.parse", return_value=feeds):
        yield feeds

@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config, patch_bot_kv_storage, mock_rss_feed):
    yield

@freeze_time("2025-01-01 00:00:00 UTC")
def test_initialization():
    from backend.bot_kv_storage import storage
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd
    action = BotRssFwd()
    assert action.config.enabled
    assert action.config.rsshub_url == "https://rsshub.example.com"
    assert len(action.config.tasks) == 1
    assert len(action._schedules) == 1
    assert storage.get("rss_fwd_time").get("/test_100_None", None) == 1735689600.0

def test_fetch_feeds():
    from backend.bot_config import config as Config
    Config.action_custom_config["BotRssFwd"]["tasks"].append({
        "endpoint": "/test2",
        "enabled": True,
        "new_topic": True,
        "category_id": 101
    })
    Config.action_custom_config["BotRssFwd"]["tasks"].append({
        "endpoint": "/test3",
        "enabled": False,
        "new_topic": True,
        "category_id": 101
    })
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd
    from feedparser import parse
    action = BotRssFwd()
    action.on_scheduled()
    parse.assert_any_call("https://rsshub.example.com/test")
    parse.assert_any_call("https://rsshub.example.com/test2")
    assert len(parse.mock_calls) == 2

@freeze_time("2021-01-01 00:00:00 UTC")
def test_warn_if_feed_in_future(caplog, mock_rss_feed):
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd
    BotRssFwd.create_post_or_topic = MagicMock()
    action = BotRssFwd()
    action.on_scheduled()
    assert f"Ignored {len(mock_rss_feed.entries)} feeds in the future." in caplog.text
    BotRssFwd.create_post_or_topic.assert_not_called()

@freeze_time("2024-12-31 00:00:00 UTC")
@pytest.mark.parametrize("set_timezone", [("UTC"), ("Asia/Shanghai")], indirect=True)
def test_ignore_past_feed(set_timezone):
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd
    from backend.bot_kv_storage import storage
    storage.set("rss_fwd_time", {"/test_100_None": 1734393600.0})
    BotRssFwd.create_post_or_topic = MagicMock()
    action = BotRssFwd()
    action.on_scheduled()
    BotRssFwd.create_post_or_topic.assert_called_once()
    assert storage.get("rss_fwd_time").get("/test_100_None", None) == 1734537600.0

@pytest.mark.parametrize("set_timezone", [("UTC"), ("Asia/Shanghai")], indirect=True)
def test_feed_time_to_local_timezone(set_timezone):
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd
    feed_time = time.gmtime(1735689600)
    local_time = BotRssFwd.feed_time_to_local_timezone(feed_time)
    assert time.mktime(local_time) == 1735689600.0

def test_custom_forward_user(mock_config):
    mock_config.action_custom_config["BotRssFwd"]["tasks"][0]["forward_username"] = "custom_user"
    mock_config.bot_accounts.append(MagicMock(id=100, username="custom_user",
        api_key="API_KEY_CUSTOM_USER", writable=True))
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd
    from backend.bot_account_manager import account_manager as AccountManager
    api = MagicMock()
    AccountManager.get_bot_client = MagicMock(side_effect={"custom_user": api}.get)
    action = BotRssFwd()
    action.create_post_or_topic(action.config.tasks[0], "title", "content")
    AccountManager.get_bot_client.assert_called_once_with("custom_user")
    api.create_topic.assert_called_once_with(title="title", raw="content", category=100, skip_validations=True)