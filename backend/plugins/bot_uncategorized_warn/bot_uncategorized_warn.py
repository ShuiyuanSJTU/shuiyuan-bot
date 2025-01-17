from ...bot_action import BotAction, on
from ...model.topic import Topic

UNCATEGORIZED_WARN_MESSAGE = "请勿选择未分类，也请不要随意发在聊聊水源，发帖前仔细阅读分类描述后选择。"

class BotUncategorizedWarn(BotAction):
    action_name = "BotUncategorizedWarn"
    @on("topic_created")
    def on_topic_created(self, topic: Topic):
        if topic.category_id == 1:
            self.api.create_post(UNCATEGORIZED_WARN_MESSAGE, topic.id, skip_validations=True)
