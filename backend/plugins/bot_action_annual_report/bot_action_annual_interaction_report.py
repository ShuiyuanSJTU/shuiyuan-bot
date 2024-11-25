import pandas as pd
from datetime import timedelta
import logging

from ...utils.redis_cache import redis_cache
from ...bot_action import on, ActionResult
from ...model.post import Post

from .base_bot_report_action import BaseBotReportAction
from .query_database import query_database

logger = logging.getLogger(__name__)


class BotInteractionReport(BaseBotReportAction):
    action_name = "BotInteractionReport"
    trigger_keyword = "我的2024互动报告"

    def get_data(self, user_id):
        try:
            # from other user
            res_from = query_database(self.api, self.config.interaction_from_query_id, {
                                      "target_user_id": user_id}, self.config.query_group)
            # to other user
            res_to = query_database(self.api, self.config.interaction_to_query_id, {
                                    "from_user_id": user_id}, self.config.query_group)
        except Exception as e:
            logger.error(e)
            raise e
        else:
            return res_from, res_to

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

    @redis_cache(ex=300, cache_key=BaseBotReportAction.cache_key_for_main_content)
    def get_reply_main_content(self, user_id, post_data, opts):
        data = self.get_data(user_id)
        if data is None:
            return "出错了，请稍后重试"

        table_from = self.render_data(data[0])
        table_to = self.render_data(data[1])

        raw = "### 这是2024年与你互动最多的用户，快和他们打个招呼吧！\n\n"
        raw += table_from
        raw += "\n\n### 2024年你与这些用户互动最多，还记得你们之间发生了什么有趣的事情吗？\n\n"
        raw += table_to
        raw += f"\n\n [size=0]{user_id},{data[0]['duration']},{data[1]['duration']}[/size]"
        return raw
