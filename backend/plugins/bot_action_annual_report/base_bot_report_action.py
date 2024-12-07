from pydantic import BaseModel

from ...bot_action import BotAction, ActionResult, on
from ...model.post import Post

class ReportOptions(BaseModel):
    override_user_id: int = -1
    override: bool = False


class BotReportActionConfig(BaseModel):
    enabled: bool = False
    admin_usernames: list[str] = []
    query_group: str = "bot"
    interaction_from_query_id: int
    interaction_to_query_id: int
    post_tag_query_id: int
    topic_read_query_id: int
    user_post_query_id: int
    user_visit_query_id: int
    working_path: str = "."


class BaseBotReportAction(BotAction):
    action_config_key = "BotAnnualReport"
    trigger_keyword = None

    def __init__(self) -> None:
        super().__init__()
        self.config: BotReportActionConfig = BotReportActionConfig(
            **self.config)
        if self.trigger_keyword is None:
            raise ValueError("trigger_keyword must be set")

    @classmethod
    def cache_key(cls, *args):
        return f"{cls.__name__}_"+'_'.join(map(lambda x: str(x).replace('_', r'\_'), args))

    def get_reply_header(self, user_id, user_name, opts: ReportOptions):
        if not opts.override:
            return f"Hi,@{user_name},\n\n"
        else:
            return f"你查询的用户ID为{user_id}，其报告如下：\n\n"

    def get_reply(self, post: Post):
        user_id = post.user_id
        user_name = post.username

        opts = ReportOptions()
        if "查询UID:" in post.raw and post.username in self.config.admin_usernames:
            for line in post.raw.split("\n"):
                if "查询UID:" in line:
                    user_id = int(line.split(":")[1].strip())
                    opts.override_user_id = user_id
                    opts.override = True
                    user_name = None
                    break

        return self.get_reply_header(user_id, user_name, opts) + self.get_reply_main_content(user_id, post, opts)

    def should_response(self, post: Post):
        if self.trigger_keyword is None:
            raise NotImplementedError
        return post.topic_id is not None and post.post_number is not None and \
            super().should_response(post) and self.trigger_keyword in post.raw

    def get_reply_main_content(self, user_id: int, post: Post, opts: ReportOptions):
        raise NotImplementedError

    @on("post_created")
    def on_post(self, post: Post):
        if self.should_response(post):
            reply_raw = self.get_reply(post)
            # print(topic_id,post_number,reply_raw)
            self.api.create_post(reply_raw,
                                 post.topic_id, post.post_number,
                                 skip_validations=True)
            return ActionResult(action_name=self.action_name, stop_propagation=True)

    @staticmethod
    def cache_key_for_main_content(action: BotAction, user_id: int, post: Post, opts: ReportOptions):
        return f"{action.action_name}_{user_id}"
