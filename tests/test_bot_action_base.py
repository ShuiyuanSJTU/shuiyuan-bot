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
        "TestBotAction": {"enabled": True},
        "TestBotAction2": {"enabled": True}}
    return mock_config_base


@pytest.fixture
def mock_bot_manager():
    with patch('backend.bot_action.BotManager') as mock_bot_manager:
        mock_bot_manager.default_bot_client = MagicMock()
        yield mock_bot_manager


def test_initialization(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    from backend.bot_action import BotActionEventHandler
    action = mock_bot_action_class()
    assert action.enabled is True
    assert action.api == mock_bot_manager.default_bot_client
    assert "post_created" in action._events_listeners
    assert isinstance(action.handle_post_created, BotActionEventHandler)
    assert action._events_listeners["post_created"].func is action.handle_post_created.func

def test_event_registration_seperate_classes(patch_bot_config, mock_config, mock_bot_action_class):
    from backend.bot_action import BotAction, on

    class TestBotAction2(BotAction):
        action_name = "TestBotAction2"

        @on("post_created")
        def handle_post_created(self, post: Post):
            return f"Handled post with id {post.id}"
    mock_config.action_custom_config["TestBotAction2"] = {"enabled": True}
    action1 = mock_bot_action_class()
    action2 = TestBotAction2()
    assert "post_created" in action1._events_listeners
    assert "post_created" in action2._events_listeners

    assert action1._events_listeners["post_created"].func is action1.handle_post_created.func
    assert action2._events_listeners["post_created"].func is action2.handle_post_created.func

    assert not action1._events_listeners["post_created"] is action2._events_listeners["post_created"]


def test_can_trigger_event(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    action = mock_bot_action_class()
    action._events_listeners["post_created"] = MagicMock()
    post = MagicMock()
    action.trigger("post_created", post)
    action._events_listeners["post_created"]\
        .assert_called_once_with(post)


def test_trigger_event_not_registered(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    action = mock_bot_action_class()
    post = MagicMock()
    # do not raise exception
    action.trigger("_event_not_registered", post)


def test_warn_when_no_event_listener(patch_bot_config, mock_bot_manager, mock_bot_action_class, caplog):
    del mock_bot_action_class.handle_post_created
    action = mock_bot_action_class()
    assert len(action._events_listeners) == 0
    assert "Action TestBotAction does not have any event listener or schedule." in caplog.text


def test_warn_when_same_action_registered_twice(patch_bot_config, mock_bot_manager, mock_bot_action_class, caplog):
    from backend.bot_manager import bot_manager as BotManager
    action1 = mock_bot_action_class
    action2 = mock_bot_action_class
    BotManager.register_bot_action(action1)
    BotManager.register_bot_action(action2)
    assert "Action TestBotAction is already registered." in caplog.text


def test_work_with_inherited_class(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    patch_bot_config.action_custom_config["TestBotAction2"] = {"enabled": True}
    from backend.bot_action import BotActionEventHandler

    class TestBotAction2(mock_bot_action_class):
        action_name = "TestBotAction2"

    action = TestBotAction2()
    assert action.enabled is True
    assert action.api == mock_bot_manager.default_bot_client
    assert "post_created" in action._events_listeners
    assert isinstance(action.handle_post_created, BotActionEventHandler)
    assert action.handle_post_created.func is mock_bot_action_class.__dict__["handle_post_created"].func


def test_work_with_inherited_class_override_method(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    patch_bot_config.action_custom_config["TestBotAction2"] = {"enabled": True}
    from backend.bot_action import BotActionEventHandler, on

    class TestBotAction2(mock_bot_action_class):
        action_name = "TestBotAction2"
        @on("post_created")
        def handle_post_created(self, post: Post):
            return f"Handled post with id {post.id} in TestBotAction2"
    
    action = TestBotAction2()
    assert action.enabled is True
    assert action.api == mock_bot_manager.default_bot_client
    assert "post_created" in action._events_listeners
    assert isinstance(action.handle_post_created, BotActionEventHandler)
    assert action.handle_post_created.func is TestBotAction2.__dict__["handle_post_created"].func
    assert not action.handle_post_created.func is mock_bot_action_class.__dict__["handle_post_created"].func
    assert action.handle_post_created.func is TestBotAction2.__dict__["handle_post_created"].func


def test_register_multiple_events_on_same_method(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    from backend.bot_action import BotActionEventHandler, on

    class TestBotAction(mock_bot_action_class):
        action_name = "TestBotAction"
        @on("post_created")
        @on("post_edited")
        def handle_post_created(self, post: Post):
            return f"Handled post with id {post.id} in TestBotAction"
    
    action = TestBotAction()
    assert action.enabled is True
    assert "post_created" in action._events_listeners
    assert "post_edited" in action._events_listeners
    assert isinstance(action.handle_post_created, BotActionEventHandler)
    assert len(action.handle_post_created.events) == 2
    assert set(action.handle_post_created.events) == set(["post_created", "post_edited"])


def test_action_without_custom_config(patch_bot_config, mock_bot_manager, mock_bot_action_class):
    from backend.bot_action import BotActionEventHandler, on

    class TestBotActionWithoutConfig(mock_bot_action_class):
        action_name = "TestBotActionWithoutConfig"
        @on("post_created")
        def handle_post_created(self, post: Post):
            pass
    
    action = TestBotActionWithoutConfig()
    assert action.enabled is False

def test_duplicate_event_registration(patch_bot_config, mock_bot_manager, mock_bot_action_class, caplog):
    from backend.bot_action import on

    class TestBotAction(mock_bot_action_class):
        action_name = "TestBotAction"
        @on("post_created")
        def handle_post_created(self, post: Post):
            pass
        @on("post_created")
        def handle_post_created2(self, post: Post):
            pass

    action = TestBotAction()
    assert len(action._events_listeners) == 1
    assert "post_created" in action._events_listeners
    assert len(action._events_listeners["post_created"].events) == 1
    assert "Event post_created already has a listener, it will be replaced." in caplog.text