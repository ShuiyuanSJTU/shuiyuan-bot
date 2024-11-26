import pytest
from unittest.mock import patch, MagicMock, create_autospec
from backend.model.post import Post
import os
import json


@pytest.fixture(scope="module")
def test_data():
    with open(os.path.join(os.path.dirname(__file__), "data/test_model_data.json")) as f:
        return {'post': json.load(f)['webhook_with_reply_to']}


@pytest.fixture
def mock_activated_actions():
    with patch('backend.bot.activated_actions', new_callable=dict) as mock_actions:
        yield mock_actions


@pytest.fixture(autouse=True)
def mock_plugins():
    mock_bot_config = create_autospec('backend.plugins')
    mock_bot_config.load_plugins = MagicMock()
    with patch.dict('sys.modules', {'backend.plugins': mock_bot_config}):
        yield


def test_trigger_event_post_created(patch_bot_config, test_data, mock_activated_actions):
    from backend.bot import BotManager
    mock_action = MagicMock()
    mock_action.enabled = True
    mock_activated_actions['test_action'] = mock_action

    BotManager.trigger_event('post_created', test_data)

    mock_action.trigger.assert_called_once()
    args, kwargs = mock_action.trigger.call_args
    assert args == ('post_created',)
    assert kwargs['post'].id == test_data['post']['id']


def test_trigger_event_action_disabled(patch_bot_config, test_data, mock_activated_actions):
    from backend.bot import BotManager
    mock_action = MagicMock()
    mock_action.enabled = False
    mock_activated_actions['test_action'] = mock_action

    BotManager.trigger_event('post_created', test_data)

    mock_action.trigger.assert_not_called()


def test_trigger_event_exception_handling(patch_bot_config, test_data, mock_activated_actions):
    from backend.bot import BotManager
    mock_action = MagicMock()
    mock_action.enabled = True
    mock_action.trigger.side_effect = Exception("Test Exception")
    mock_activated_actions['test_action'] = mock_action

    with patch('backend.bot.logging.error') as mock_logging_error:
        BotManager.trigger_event('post_created', test_data)
        mock_logging_error.assert_called_once_with(
            "Error when triggering event post_created for action test_action: Test Exception", exc_info=mock_action.trigger.side_effect)


def test_limited_mode(patch_bot_config, test_data, mock_activated_actions):
    from backend.bot import BotManager
    mock_action = MagicMock()
    mock_action.enabled = True
    mock_activated_actions['test_action'] = mock_action
    patch_bot_config.config.limited_mode = True
    patch_bot_config.config.limited_usernames = ['test_user']

    test_data['post']['username'] = 'test_user'
    BotManager.trigger_event('post_created', test_data)
    mock_action.trigger.assert_called_once()

    test_data['post']['username'] = 'other_user'
    BotManager.trigger_event('post_created', test_data)
    mock_action.trigger.assert_called_once()
