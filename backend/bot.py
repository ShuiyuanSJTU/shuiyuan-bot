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
                        f"Error when triggering event {event} for action {action_name}: {e}")
        return return_values

    # def __init__(self, api: BotAPI) -> None:
    #     self.bot_api = api
    #     self.bot_username: str = api.username
    #     self.bot_actions: List[BotAction] = []

    # def register_bot_action(self, bot_action: Type[BotAction]):
    #     action = bot_action(self.bot_api,self.bot_username)
    #     self.bot_actions.append(action)

    # def respond(self,post: Post,allow_muiltiple_response=False):
    #     for bot_action in self.bot_actions:
    #         action_taken = bot_action.on_post_created(post)
    #         if action_taken and not allow_muiltiple_response:
    #             break

    # def should_respond(self,post: Post,allow_muiltiple_response=False):
    #     # ignore bot
    #     if post.username == self.bot_username:
    #         return False
    #     # check if bot is mentioned
    #     if re.search(rf"(^|\s)@{self.bot_username}\b", post.raw):
    #         return True
    #     # check if is reply to bot
    #     reply_to_username = post.reply_to_user.username \
    #             if post.reply_to_user is not None else None
    #     if reply_to_username == self.bot_username:
    #         return True
    #     return False

    # def on_post_created(self,post_data: dict):
    #     post = Post(**post_data)
    #     if self.should_respond(post):
    #         self.respond(post)
