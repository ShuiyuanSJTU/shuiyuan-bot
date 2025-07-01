import pytest
from unittest.mock import MagicMock, patch
from backend.model.post import Post

@pytest.fixture
def mock_bot_action_class(patch_bot_config):
    from backend.bot_action import BotAction, on, scheduled

    class TestBotAction(BotAction):
        action_name = "TestBotAction"

        @on("post_created")
        def handle_post_created(self, post: Post):
            return f"Handled post with id {post.id}"
        
        @scheduled('interval', minutes=2, id='my_job_id')
        def scheduled_job(self):
            return "Scheduled job"
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

@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config, mock_bot_manager):
    yield

def test_initialization(mock_bot_manager, mock_bot_action_class):
    from backend.bot_action import BotActionEventHandler
    action = mock_bot_action_class()
    assert action.enabled is True
    assert action.api == mock_bot_manager.default_bot_client
    assert "post_created" in action._events_listeners
    assert isinstance(action.handle_post_created, BotActionEventHandler)
    assert action._events_listeners["post_created"].func is action.handle_post_created.func
    assert isinstance(action.scheduled_job, BotActionEventHandler)
    assert action._schedules[0][1].func is action.scheduled_job.func

def test_event_registration_seperate_classes(mock_config, mock_bot_action_class):
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

    assert action1._events_listeners["post_created"] is not action2._events_listeners["post_created"]

def test_can_trigger_event(mock_bot_action_class):
    action = mock_bot_action_class()
    action._events_listeners["post_created"] = MagicMock()
    post = MagicMock()
    action.trigger("post_created", post)
    action._events_listeners["post_created"]\
        .assert_called_once_with(post)

def test_trigger_event_not_registered(mock_bot_action_class):
    action = mock_bot_action_class()
    post = MagicMock()
    # do not raise exception
    action.trigger("_event_not_registered", post)

def test_warn_when_no_event_listener(mock_bot_action_class, caplog):
    del mock_bot_action_class.handle_post_created
    del mock_bot_action_class.scheduled_job
    action = mock_bot_action_class()
    assert len(action._events_listeners) == 0
    assert "Action TestBotAction does not have any event listener or schedule." in caplog.text

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

def test_work_with_inherited_class_override_method(mock_config, mock_bot_manager, mock_bot_action_class):
    mock_config.action_custom_config["TestBotAction2"] = {"enabled": True}
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
    assert action.handle_post_created.func is not mock_bot_action_class.__dict__["handle_post_created"].func
    assert action.handle_post_created.func is TestBotAction2.__dict__["handle_post_created"].func

def test_register_multiple_events_on_same_method(mock_bot_action_class):
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

def test_action_without_custom_config(mock_bot_action_class):
    from backend.bot_action import on

    class TestBotActionWithoutConfig(mock_bot_action_class):
        action_name = "TestBotActionWithoutConfig"
        @on("post_created")
        def handle_post_created(self, post: Post):
            pass
    
    action = TestBotActionWithoutConfig()
    assert action.enabled is False

def test_duplicate_event_registration(mock_bot_action_class, caplog):
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

def test_warn_config_not_found(caplog):
    from backend.bot_action import BotAction, on

    class TestBotAction2(BotAction):
        action_name = "TestBotAction2"
        action_config_key = "TestBotAction2Config"

        @on("post_created")
        def handle_post_created(self, post: Post):
            return
    
    action = TestBotAction2()
    assert not action.enabled
    assert "Action TestBotAction2 does not have an enabled field in the config, it will be disabled by default." in caplog.text
    assert "Please notice that the action config key TestBotAction2Config is different from the action name TestBotAction2." in caplog.text

def test_event_handler_can_be_called_directly(mock_bot_action_class):
    action = mock_bot_action_class()
    post = MagicMock()
    assert action.handle_post_created(post) == f"Handled post with id {post.id}"