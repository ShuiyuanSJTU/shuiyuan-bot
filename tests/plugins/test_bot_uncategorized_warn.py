import pytest
import os
import json
from unittest.mock import MagicMock, patch
from backend.model.topic import Topic
from datetime import datetime, timedelta

@pytest.fixture
def init_table(mock_config):
    from backend.db import DBManager
    import backend.plugins.bot_uncategorized_warn.bot_uncategorized_warn
    db_manager = DBManager()
    db_manager.init_tables()
    with db_manager.scoped_session() as session:
        yield

@pytest.fixture(scope="module")
def test_data():
    data = {}
    with open(os.path.join(os.path.dirname(__file__), "../data/test_model_post_data.json")) as f:
        data['post'] = json.load(f)['api']
    with open(os.path.join(os.path.dirname(__file__), "../data/test_model_topic_data.json")) as f:
        data['topic'] = json.load(f)['topic']
    return data

@pytest.fixture
def mock_db_session():
    with patch('backend.db.DBManager.scoped_session', autospec=True) as mock_session:
        yield mock_session

@pytest.fixture
def mock_config(mock_config_base):
    mock_config_base.action_custom_config = {
        "BotUncategorizedWarn": {
            "enabled": True,
        }
    }
    return mock_config_base

@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config, mock_db_session, init_table):
    yield

def test_on_topic_created(test_data):
    from backend.plugins.bot_uncategorized_warn.bot_uncategorized_warn import BotUncategorizedWarn, UncategorizedTopicWarningRecord, WarningStatus
    action = BotUncategorizedWarn()
    action.api = MagicMock()
    action.api.create_post.return_value = {'id': 123}

    topic = Topic(**test_data['topic'])
    action.on_topic_created(topic)

    action.api.create_post.assert_called_once_with("请勿选择未分类，也请不要随意发在聊聊水源，发帖前仔细阅读分类描述后选择。", test_data['topic']['id'], skip_validations=True)
    record = UncategorizedTopicWarningRecord.find(topic_id=test_data['topic']['id'])
    assert record is not None
    assert record.post_id == 123
    assert record.status == WarningStatus.PENDING

def test_check_warnings_close_topic(test_data):
    from backend.plugins.bot_uncategorized_warn.bot_uncategorized_warn import BotUncategorizedWarn, UncategorizedTopicWarningRecord, WarningStatus
    action = BotUncategorizedWarn()

    UncategorizedTopicWarningRecord(topic_id=1, post_id=123, status=WarningStatus.PENDING, created_at=datetime.now() - timedelta(minutes=40)).save()

    action.api = MagicMock()
    action.api.get_topic_by_id.return_value = test_data['topic']

    action.check_warnings()

    record_pending = UncategorizedTopicWarningRecord.find(topic_id=1)
    assert record_pending.status == WarningStatus.EXPIRED
    action.api.close_topic.assert_called_once_with(test_data['topic']['id'])

def test_check_warnings_remove_warning(test_data):
    from backend.plugins.bot_uncategorized_warn.bot_uncategorized_warn import BotUncategorizedWarn, UncategorizedTopicWarningRecord, WarningStatus
    action = BotUncategorizedWarn()

    UncategorizedTopicWarningRecord(topic_id=1, post_id=123, status=WarningStatus.PENDING, created_at=datetime.now() - timedelta(minutes=40)).save()

    action.api = MagicMock()
    new_topic = test_data['topic'].copy()
    new_topic['category_id'] = 2
    action.api.get_topic_by_id.return_value = new_topic

    action.check_warnings()

    record_pending = UncategorizedTopicWarningRecord.find(topic_id=1)
    assert record_pending.status == WarningStatus.REMOVED
    action.api.delete_post.assert_called_once_with(record_pending.post_id)