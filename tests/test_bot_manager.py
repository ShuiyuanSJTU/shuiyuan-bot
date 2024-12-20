import pytest
from unittest.mock import patch, MagicMock, create_autospec
import os
import json


@pytest.fixture(scope="module")
def test_data():
    with open(os.path.join(os.path.dirname(__file__), "data/test_model_data.json")) as f:
        return {'post': json.load(f)['webhook_with_reply_to']}

@pytest.fixture
def mock_activated_actions():
    with patch('backend.bot_manager.bot_manager.activated_actions', new_callable=dict) as mock_actions:
        yield mock_actions

@pytest.fixture
def mock_bot_action_class(patch_bot_config):
    from backend.bot_action import BotAction, on, scheduled

    class TestBotAction(BotAction):
        action_name = "TestBotAction"

        @on("post_created")
        def handle_post_created(self, post):
            return f"Handled post with id {post.id}"
        
        @scheduled('interval', minutes=2, id='my_job_id')
        def scheduled_job(self):
            return "Scheduled job"
    return TestBotAction

@pytest.fixture(autouse=True)
def mock_plugins():
    mock_plugins = create_autospec('backend.plugins')
    mock_plugins.load_plugins = MagicMock()
    with patch.dict('sys.modules', {'backend.plugins': mock_plugins}):
        yield

def test_trigger_event_post_created(patch_bot_config, test_data, mock_activated_actions):
    from backend.bot_manager import bot_manager as BotManager
    mock_action = MagicMock()
    mock_action.enabled = True
    mock_activated_actions['test_action'] = mock_action

    BotManager.trigger_event('post_created', test_data)

    mock_action.trigger.assert_called_once()
    args, kwargs = mock_action.trigger.call_args
    assert args == ('post_created',)
    assert kwargs['post'].id == test_data['post']['id']

def test_trigger_event_action_disabled(patch_bot_config, test_data, mock_activated_actions):
    from backend.bot_manager import bot_manager as BotManager
    mock_action = MagicMock()
    mock_action.enabled = False
    mock_activated_actions['test_action'] = mock_action

    BotManager.trigger_event('post_created', test_data)

    mock_action.trigger.assert_not_called()

def test_trigger_event_exception_handling(patch_bot_config, test_data, mock_activated_actions):
    from backend.bot_manager import bot_manager as BotManager
    mock_action = MagicMock()
    mock_action.enabled = True
    mock_action.trigger.side_effect = Exception("Test Exception")
    mock_activated_actions['test_action'] = mock_action

    with patch('backend.bot_manager.logging.error') as mock_logging_error:
        BotManager.trigger_event('post_created', test_data)
        mock_logging_error.assert_called_once_with(
            "Error when triggering event post_created for action test_action: Test Exception", exc_info=mock_action.trigger.side_effect)

def test_limited_mode(patch_bot_config, test_data, mock_activated_actions):
    from backend.bot_manager import bot_manager as BotManager
    mock_action = MagicMock()
    mock_action.enabled = True
    mock_activated_actions['test_action'] = mock_action
    patch_bot_config.limited_mode = True
    patch_bot_config.limited_usernames = ['test_user']

    test_data['post']['username'] = 'test_user'
    BotManager.trigger_event('post_created', test_data)
    mock_action.trigger.assert_called_once()

    test_data['post']['username'] = 'other_user'
    BotManager.trigger_event('post_created', test_data)
    mock_action.trigger.assert_called_once()

def test_warn_when_same_action_registered_twice(mock_bot_action_class, caplog):
    from backend.bot_manager import bot_manager as BotManager
    action1 = mock_bot_action_class
    action2 = mock_bot_action_class
    BotManager.register_bot_action(action1)
    BotManager.register_bot_action(action2)
    assert "Action TestBotAction is already registered." in caplog.text

def test_register_scheduled_jobs(patch_bot_config, mock_bot_action_class):
    from backend.bot_manager import bot_manager as BotManager
    patch_bot_config.action_custom_config["TestBotAction"] = {"enabled": True}
    BotManager.register_bot_action(mock_bot_action_class)
    scheduler = MagicMock()
    scheduler.add_job = MagicMock()
    BotManager.register_jobs_to_scheduler(scheduler)
    scheduler.add_job.call_count == 1
    call_args = scheduler.add_job.call_args
    assert call_args[0][0].func == mock_bot_action_class.scheduled_job.func
    assert call_args[0][1] == 'interval'
    assert call_args[1]['id'] == 'my_job_id'
    assert call_args[1]['minutes'] == 2

def test_warn_when_not_registered_to_scheduler(patch_bot_config, mock_bot_action_class, test_data, caplog):
    from backend.bot_manager import bot_manager as BotManager
    patch_bot_config.action_custom_config["TestBotAction"] = {"enabled": True}
    BotManager.register_bot_action(mock_bot_action_class)
    BotManager.trigger_event('post_created', test_data)
    assert "There are schedules that are not registered, please make sure you have registered the scheduler." in caplog.text