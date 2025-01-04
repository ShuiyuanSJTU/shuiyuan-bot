from ...bot_action import BotAction, on
from ...model.post import Post
from ...bot_account_manager import account_manager as AccountManager

from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class ForwardTask(BaseModel):
    source_topic_id: int
    target_topic_id: int
    forward_username: str

class BotForward(BotAction):
    action_name = "BotForward"

    def __init__(self):
        super().__init__()
        self.forward_tasks: list[ForwardTask] = [ForwardTask(**task) for task in self.config.get("forward_tasks", [])]
        if len(self.forward_tasks) == 0:
            logger.warning("No forward task is configured.")
        self.watching_topic_ids = set([task.source_topic_id for task in self.forward_tasks])

    @on("post_created")
    def on_post_created(self, post: Post):
        if post.post_type != 1:
            return
        if post.topic_id in self.watching_topic_ids:
            for task in self.forward_tasks:
                if task.source_topic_id == post.topic_id:
                    self.forward_post(post, task.target_topic_id, task.forward_username)

    def forward_post(self, post: Post, target_topic_id: int, forward_username: str):
        bot_client = AccountManager.get_bot_client(forward_username)
        bot_client.create_post(post.raw, target_topic_id, skip_validations=True)