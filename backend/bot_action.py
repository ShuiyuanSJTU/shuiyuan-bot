from .discourse_api import BotAPI
from .model.post import Post
from .bot_account_manager import account_manager as BotManager
from .bot_config import config as Config
from .utils.bot_post_check import post_created_by_bot, post_mention_bot, post_reply_to_bot
import logging
from collections import namedtuple
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ActionResult(BaseModel):
    action_name: str
    responsed: bool = False
    stop_propagation: bool = False
    success: bool = True
    message: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class BotAction:
    action_name = "BotActionBase"
    action_config_key = ""
    _events_listeners = {}

    def __init__(self) -> None:
        self.priority: int = 0
        self._load_config()
        if self.enabled:
            self.api: BotAPI = BotManager.default_bot_client
            self._register_events()

    def _load_config(self):
        _action_config_key = self.action_config_key or self.action_name
        self.config: dict = Config.action_custom_config.get(
            _action_config_key, {})
        if 'enabled' not in self.config:
            logger.warning(
                f"Action {self.action_name} does not have an enabled field in the config, it will be disabled by default.")
            if _action_config_key != self.action_name:
                logger.warning(
                    f"Please notice that the action config key {_action_config_key} is different from the action name {self.action_name}.")
        self.enabled: bool = self.config.get('enabled', False)

    def _register_events(self):
        self._events_listeners: dict[str, callable] = {}
        self._schedules: list[tuple[ScheduleArgs, callable]] = []
        for attr in dir(self):
            if not attr.startswith("__"):
                obj = getattr(self, attr)
                if isinstance(obj, BotActionEventHandler):
                    for event in obj.events:
                        if event in self._events_listeners:
                            logger.warning(
                                f"Event {event} already has a listener, it will be replaced.")
                        self._events_listeners[event] = obj
                    for schedule in obj.schedules:
                        self._schedules.append((schedule, obj))
        if len(self._events_listeners) == 0 and len(self._schedules) == 0:
            logger.warning(
                f"Action {self.action_name} does not have any event listener or schedule.")

    def should_response(self, post: Post):
        return not post_created_by_bot(post) and (post_mention_bot(post, self.api.username) or post_reply_to_bot(post, self.api.username))

    def trigger(self, event: str, *args, **kwargs):
        if event in self._events_listeners:
            return self._events_listeners[event](*args, **kwargs)
        return None

def scheduled(*args, **kwargs):
    """
    Decorator to trigger a method on a schedule.

    Parameters will be passed to the `add_job` method of `apscheduler.schedulers.base.BaseScheduler`.

    This decorator can be used multiple times on the same method, then the method will be triggered on multiple schedules. Schedule will not be registered if the action is disabled.

    No parameters will be passed to the handler when triggered by the scheduler.
    """
    def wrapper(func: callable):
        descriptor = func if isinstance(func, BotActionEventDescriptor) else BotActionEventDescriptor(func)
        descriptor.append_schedule(ScheduleArgs(args, kwargs))
        return descriptor
    return wrapper

def on(event: str):
    """
    Decorator to bind a method as a handler to an Discourse event.

    This decorator can be used multiple times on the same method, then the method will be triggered on multiple events. Event will not be registered if the action is disabled.

    Parameters passed to the handler depend on the event type, please refer to the Discourse webhook documentation.
    """
    def wrapper(func: callable):
        descriptor = func if isinstance(func, BotActionEventDescriptor) else BotActionEventDescriptor(func)
        descriptor.append_event(event)
        return descriptor
    return wrapper

ScheduleArgs = namedtuple("ScheduleArgs", ["args", "kwargs"])

class BotActionEventDescriptor:
    def __get__(self, instance, owner):
        return BotActionEventHandler(instance, self.func, self.events, self.schedules)

    def __init__(self, func: callable):
        self.events = []
        self.schedules = []
        self.func = func

    def append_event(self, event: str):
        self.events.append(event)
    
    def append_schedule(self, schedule: str):
        self.schedules.append(schedule)

class BotActionEventHandler:
    def __init__(self, action: BotAction, func: callable,
                  events: Optional[tuple[str]] = None,
                  schedules: Optional[tuple[ScheduleArgs]] = None):
        self.action = action
        self.events = [] if events is None else events
        self.schedules = [] if schedules is None else schedules
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(self.action, *args, **kwargs)
