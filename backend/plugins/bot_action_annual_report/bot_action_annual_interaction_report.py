import pandas as pd
import logging

from ...utils.redis_cache import redis_cache

from .base_bot_report_action import BaseBotReportAction
from .query_database import query_database, retry_when_timeout

logger = logging.getLogger(__name__)

class BotInteractionReport(BaseBotReportAction):
    action_name = "BotInteractionReport"
    trigger_keyword = "我的2024互动报告"

    @retry_when_timeout()
    def get_data_from(self, user_id):
        # from other user
        return query_database(self.api, self.config.interaction_from_query_id, {
                                    "target_user_id": user_id}, self.config.query_group)

    @retry_when_timeout()
    def get_data_to(self, user_id):
        # to other user
        return query_database(self.api, self.config.interaction_to_query_id, {
                                "from_user_id": user_id}, self.config.query_group)

    @classmethod
    def render_user(cls, user_info):
        username = user_info['username']
        avatar_template = user_info['avatar_template']
        avatar_src = avatar_template.format(size=48)
        avatar_html = '<img loading="lazy" alt="{username}" width="24" height="24" src="{src}" class="avatar" title="{username}">'.format(
            username=username, src=avatar_src)
        return f"{avatar_html} @{username}"

    @classmethod
    def render_data(cls, data):
        usersinfo_by_id = {u['id']: u for u in data['relations']['user']}
        rows = data['rows']
        df = pd.DataFrame(columns=['', '', '表情', '点赞', '回复'])
        for i in range(min(3, len(rows))):
            row = rows[i]
            df.loc[i] = [
                i+1, cls.render_user(usersinfo_by_id[row[0]]), row[2], row[3], row[4]]
        return df.to_markdown(index=False, numalign="center")

    @redis_cache(ex=600, cache_key=lambda self, user_id: f"{self.action_name}_from_{user_id}")
    def get_table_from(self, user_id):
        return self.render_data(self.get_data_from(user_id))
    
    @redis_cache(ex=600, cache_key=lambda self, user_id: f"{self.action_name}_to_{user_id}")
    def get_table_to(self, user_id):
        return self.render_data(self.get_data_to(user_id))

    def get_reply_main_content(self, user_id, post_data, opts):
        resopnse = []

        try:
            table_from = self.get_table_from(user_id)
            resopnse.append("### 这是2024年与你互动最多的用户，快和他们打个招呼吧！")
            resopnse.append(table_from)
        except Exception as e:
            logger.error(e)

        try:
            table_to = self.get_table_to(user_id)
            resopnse.append("### 2024年你与这些用户互动最多，还记得你们之间发生了什么有趣的事情吗？")
            resopnse.append(table_to)
        except Exception as e:
            logger.error(e)
        
        return "\n\n".join(resopnse)
