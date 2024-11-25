import pytest
from unittest.mock import MagicMock, patch
from backend.model.post import Post


@pytest.fixture
def mock_bot_action_class(patch_bot_config):
    from backend.bot_action import BotAction, on

    class TestBotAction(BotAction):
        action_name = "TestBotAction"

        @on("post_created")
        def handle_post_created(self, post: Post):
            return f"Handled post with id {post.id}"
    return TestBotAction


@pytest.fixture
def mock_config(mock_config_base):
    mock_config_base.action_custom_config = {
        "TestBotAction": {"enabled": True}}
    return mock_config_base


@pytest.fixture
def mock_bot_manager():
    with patch('backend.bot_action.BotManager') as mock_bot_manager:
        mock_bot_manager.default_bot_client = MagicMock()
        yield mock_bot_manager


def test_bot_action_initialization(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    from backend.bot_action import BotActionEventWrapper
    action = mock_bot_action_class()
    assert action.enabled is True
    assert action.api == mock_bot_manager.default_bot_client
    assert "post_created" in action._events_listener
    assert isinstance(action.handle_post_created, BotActionEventWrapper)


def test_bot_action_event_registration_seperate_classes(patch_bot_config, mock_config, mock_bot_action_class):
    from backend.bot_action import BotAction, on

    class TestBotAction2(BotAction):
        action_name = "TestBotAction2"

        @on("post_created")
        def handle_post_created(self, post: Post):
            return f"Handled post with id {post.id}"
    mock_config.action_custom_config["TestBotAction2"] = {"enabled": True}
    action1 = mock_bot_action_class()
    action2 = TestBotAction2()
    assert "post_created" in action1._events_listener
    assert "post_created" in action2._events_listener

    assert action1._events_listener["post_created"] is action1.handle_post_created.func
    assert action2._events_listener["post_created"] is action2.handle_post_created.func

    assert not action1._events_listener["post_created"] is action2._events_listener["post_created"]


def test_bot_action_can_trigger_event(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    action = mock_bot_action_class()
    action._events_listener["post_created"] = MagicMock()
    post = MagicMock()
    action.trigger("post_created", post)
    action._events_listener["post_created"].assert_called_once_with(
        action, post)


def test_bot_action_trigger_event_not_registered(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    action = mock_bot_action_class()
    post = MagicMock()
    # do not raise exception
    action.trigger("_event_not_registered", post)


def test_bot_action_warning_when_no_event_listener(patch_bot_config, mock_bot_manager, mock_bot_action_class, caplog):
    del mock_bot_action_class.handle_post_created
    action = mock_bot_action_class()
    assert len(action._events_listener) == 0
    assert "Action TestBotAction does not have any event listener." in caplog.text


def test_bot_action_warning_when_same_action_registered_twice(patch_bot_config, mock_bot_manager, mock_bot_action_class, caplog):
    from backend.bot_action import register_bot_action
    action1 = mock_bot_action_class
    action2 = mock_bot_action_class
    register_bot_action(action1)
    register_bot_action(action2)
    assert "Action TestBotAction is already registered." in caplog.text
