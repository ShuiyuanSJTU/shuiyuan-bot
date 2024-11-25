from ...bot_action import BotAction, on
from ...model.post import Post
import json


class BotEcho(BotAction):
    action_name = "BotEcho"

    def get_reply(self, post: Post):
        return f"```\n{json.dumps(post.model_dump(), indent=4, ensure_ascii=False)}\n```"

    @on("post_created")
    def on_post_created(self, post: Post):
        if self.should_response(post):

            reply_text = self.get_reply(post)

            self.api.create_post(reply_text, post.topic_id,
                                 post.post_number, skip_validations=True)

    @on("ping")
    def on_ping(self, *args, **kwargs):
        return "pong"
