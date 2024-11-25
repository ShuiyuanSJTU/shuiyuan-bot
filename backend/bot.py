import re
import logging
from typing import Optional, List, Type
from .bot_action import BotAction, activated_actions, ActionResult
from .discourse_api import BotAPI
from .model.post import Post
from .bot_config import config as Config
from . import plugins

plugins.load_plugins()


class BotManager:
    @classmethod
    def trigger_event(cls, event: str, data: dict):
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
        for action_name, action in activated_actions.items():
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