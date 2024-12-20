import re
import logging
from typing import Optional, List, Type
from .utils.singleton import Singleton
from .bot_action import BotAction, ActionResult
from .discourse_api import BotAPI
from .model.post import Post
from .bot_config import config as Config

logger = logging.getLogger(__name__)

@Singleton
class BotManager:
    def __init__(self):
        self.registered_actions: dict[str, BotAction] = {}
        self.activated_actions: dict[str, BotAction] = {}

    def register_bot_action(self, action_cls: Type[BotAction]):
        if action_cls.action_name in self.registered_actions:
            logger.warning(f"Action {action_cls.action_name} is already registered.")
        else:
            logger.info(f"Action {action_cls.action_name} is registered.")
            action_inst = action_cls()
            self.registered_actions[action_cls.action_name] = action_inst
            if action_inst.enabled:
                self.activated_actions[action_cls.action_name] = action_inst


    def trigger_event(self, event: str, data: dict):
        args = []
        kwargs = {}
        match event:
            case "post_created":
                post = Post(**data['post'])
                if Config.limited_mode and post.username not in Config.limited_usernames:
                    return
                kwargs['post'] = post
            case "ping":
                pass

        return_values = []
        for action_name, action in self.activated_actions.items():
            if action.enabled:
                try:
                    action_return = action.trigger(event, *args, **kwargs)
                    if action_return is not None:
                        if isinstance(action_return, ActionResult):
                            return_values.append(action_return.message)
                            if action_return.stop_propagation:
                                break
                        else:
                            return_values.append(action_return)
                except Exception as e:
                    logging.error(
                        f"Error when triggering event {event} for action {action_name}: {e}", exc_info=e)
        return return_values

bot_manager = BotManager()
