from .discourse_api import BotAPI
from .model.post import Post
from .bot_account_manager import account_manager as BotManager
from .bot_config import config as Config
from . import utils
import logging
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

activated_actions: dict[str, 'BotAction'] = {}


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
    _events_listener = {}

    def __init__(self) -> None:
        self.priority: int = 0
        self._load_config()
        if self.enabled:
            self.api: BotAPI = BotManager.default_bot_client
            self._register_events_listener()

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

    def _register_events_listener(self):
        self._events_listener: dict[str, callable] = {}
        for attr in dir(self):
            if not attr.startswith("__"):
                obj = getattr(self, attr)
                if isinstance(obj, BotActionEventHandler):
                    event = obj.event
                    if event in self._events_listener:
                        logger.warning(
                            f"Event {event} already has a listener, it will be replaced.")
                    self._events_listener[event] = obj
        if len(self._events_listener) == 0:
            logger.warning(
                f"Action {self.action_name} does not have any event listener.")

    def should_response(self, post: Post):
        return not utils.post_created_by_bot(post) and (utils.post_mention_bot(post, self.api.username) or utils.post_reply_to_bot(post, self.api.username))

    def on_post_created(self, post: Post):
        raise NotImplementedError()

    def trigger(self, event: str, *args, **kwargs):
        if event in self._events_listener:
            return self._events_listener[event](*args, **kwargs)
        return None

def on(event: str):
    def wrapper(func: callable):
        return BotActionEventDescriptor(event, func)
    return wrapper

class BotActionEventDescriptor:
    def __get__(self, instance, owner):
        return BotActionEventHandler(instance, self.event, self.func)

    def __init__(self, event: str, func: callable):
        self.event = event
        self.func = func

class BotActionEventHandler:
    def __init__(self, action: BotAction, event: str, func: callable):
        self.action = action
        self.event = event
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(self.action, *args, **kwargs)

    def __eq__(self, other):
        return self.event == other.event and\
              self.func is other.func and self.action is other.action


def register_bot_action(action: Type[BotAction]):
    if action.action_name in activated_actions:
        logger.warning(f"Action {action.action_name} is already registered.")
    else:
        logger.info(f"Action {action.action_name} is registered.")
        activated_actions[action.action_name] = action()
