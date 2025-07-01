import pytest
from unittest.mock import patch, MagicMock
import os
import time
import feedparser

@pytest.fixture
def init_table(mock_config):
    from backend.db import DBManager
    import backend.plugins.bot_rss_fwd.bot_rss_fwd  # noqa: F401
    db_manager = DBManager()
    db_manager.init_tables()
    with db_manager.scoped_session():
        yield

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

def test_initialization():
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd
    action = BotRssFwd()
    assert action.config.enabled
    assert action.config.rsshub_url == "https://rsshub.example.com"
    assert len(action.config.tasks) == 1
    assert len(action._schedules) == 1

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
    api.create_topic.side_effect = Exception("Stop execution")
    AccountManager.get_bot_client = MagicMock(side_effect={"custom_user": api}.get)
    action = BotRssFwd()
    with pytest.raises(Exception, match="Stop execution"):
        action.create_post_or_topic(action.config.tasks[0], "title", "content")
    AccountManager.get_bot_client.assert_called_once_with("custom_user")
    api.create_topic.assert_called_once_with(title="title", raw="content", category=100, skip_validations=True)

def test_filter_feed(init_table, mock_rss_feed):
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd, RssFwdRecord
    all_feeds = mock_rss_feed.entries
    action = BotRssFwd()
    feeds = action.filter_feed(all_feeds, action.config.tasks[0])
    assert len(feeds) == 2
    RssFwdRecord(task_id="/test_100_None", guid=all_feeds[0].guid).save()
    feeds = action.filter_feed(all_feeds, action.config.tasks[0])
    assert len(feeds) == 1
    assert feeds[0].guid == all_feeds[1].guid

def test_record_feed(init_table, mock_rss_feed):
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd, RssFwdRecord
    action = BotRssFwd()
    action.record_feed(action.config.tasks[0], mock_rss_feed.entries[0])
    assert RssFwdRecord.where(task_id="/test_100_None").count() == 1
    record = RssFwdRecord.find(task_id="/test_100_None")
    assert record.guid == mock_rss_feed.entries[0].guid
    assert record.topic_id is None
    assert record.post_id is None
    post = MagicMock()
    post.id = 100
    post.topic_id = 200
    action.record_feed(action.config.tasks[0], mock_rss_feed.entries[1], post)
    record = RssFwdRecord.find(task_id="/test_100_None", guid=mock_rss_feed.entries[1].guid)
    assert record.topic_id == 200
    assert record.post_id == 100
    assert RssFwdRecord.where(task_id="/test_100_None").count() == 2

def test_handle_new_task(init_table):
    from backend.plugins.bot_rss_fwd.bot_rss_fwd import BotRssFwd, RssFwdRecord
    action = BotRssFwd()
    assert action.config.tasks[0].is_new_task
    action.on_scheduled()
    assert RssFwdRecord.where(task_id="/test_100_None").count() == 2
    assert not action.config.tasks[0].is_new_task