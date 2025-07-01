import pandas as pd
from datetime import timedelta
import os
import pickle
import logging

from ...utils.redis_cache import redis_cache

from .base_bot_report_action import BaseBotReportAction
from .preprocess_data import preprocess_visit_data
from .query_database import query_database, query_database_paged

logger = logging.getLogger(__name__)


class BotReadReport(BaseBotReportAction):
    action_name = "BotReadReport"
    trigger_keyword = "我的2024阅读报告"

    def __init__(self) -> None:
        super().__init__()
        self.load_global_report_data()

    def load_global_report_data(self):
        processed_data_path = os.path.join(
            self.config.working_path, "visit_report_processed.pkl")
        if not os.path.exists(processed_data_path):
            logger.info("Processed data not found, querying database...")
            raw_data = query_database_paged(self.api, self.config.user_visit_query_id, {
            }, self.config.query_group, page_size=500000)
            logger.info("Query finished, preprocessing data...")
            preprocess_visit_data(raw_data, processed_data_path)
        with open(processed_data_path, "rb") as f:
            self.global_report_data: pd.DataFrame = pickle.load(f)

    def get_visit_data(self, user_id):
        return dict(self.global_report_data.loc[user_id])

    def get_topic_read_data(self, user_id):
        try:
            res = query_database(self.api, self.config.topic_read_query_id, {
                                 "user_id": user_id}, self.config.query_group)
        except Exception as e:
            logger.error(e)
            raise e
        else:
            return res

    @staticmethod
    def render_post_link(post_id, title=''):
        escaped_title = title.replace("\\", "\\\\").replace(
            '|', '\|').replace('[', '\[').replace(']', '\]')
        return f"[{escaped_title}](/t/{post_id}?silent=true)"

    @staticmethod
    def convert_milliseconds_to_readable_time(milliseconds):
        if milliseconds == 86400000:
            return "大于1天"

        seconds = milliseconds / 1000
        time_obj = timedelta(seconds=seconds)
        hours = time_obj.seconds // 3600
        minutes = (time_obj.seconds // 60) % 60

        if hours >= 2:
            return f"{hours}小时"
        else:
            return f"{hours}小时{minutes}分钟"

    @classmethod
    def render_data(cls, data):
        topicinfo_by_id = {u['id']: u for u in data['relations']['topic']}
        rows = data['rows']
        df = pd.DataFrame(columns=['话题', '阅读时间'])
        for i in range(min(5, len(rows))):
            row = rows[i]
            df.loc[i] = [cls.render_post_link(
                row[0], topicinfo_by_id[row[0]]['title']), cls.convert_milliseconds_to_readable_time(row[1])]
        return df.to_markdown(index=False, numalign="center", stralign="center")

    @redis_cache(ex=600, cache_key=BaseBotReportAction.cache_key_for_main_content)
    def get_reply_main_content(self, user_id, post_data, opts):
        # posts_read, time_read, days_visited, posts_read_percentile, time_read_percentile, days_visited_percentile
        visit_data = self.get_visit_data(user_id)

        topic_read_data = self.get_topic_read_data(user_id)
        if topic_read_data is None:
            return "出错了，请稍后重试"

        table = self.render_data(topic_read_data)

        raw = ''

        if visit_data['days_visited'] >= 365:
            raw += "你2024年一天不落地打开水源，想必水源已经成为你生活的一部分吧！\n\n"
        else:
            days_visited_percentile = int(
                (1-visit_data['days_visited_rank']/len(self.global_report_data))*100)
            raw += f"你2024年共打开水源{visit_data['days_visited']:.0f}天，超过了{days_visited_percentile:.0f}%的用户，期待明年能在水源见到更活跃的你！\n\n"

        raw += f"你2024年共阅读{visit_data['posts_read']:.0f}条帖子，"
        if visit_data['posts_read_rank'] <= 100:
            raw += f"在所有用户中排名第{visit_data['posts_read_rank']:.0f}!\n\n"
        else:
            posts_read_percentile = int(
                (1-(visit_data['posts_read_rank']-1)/len(self.global_report_data))*1000)/10
            raw += f"超过{posts_read_percentile:.1f}%的水源用户\n\n"

        raw += f"你2024年共阅读了{visit_data['time_read']/3600:.0f}小时，"
        if visit_data['time_read_rank'] <= 100:
            raw += f"在所有用户中排名第{visit_data['time_read_rank']:.0f}!\n\n"
        else:
            time_read_percentile = int(
                (1-(visit_data['time_read_rank']-1)/len(self.global_report_data))*1000)/10
            raw += f"超过{time_read_percentile:.1f}%的水源用户\n\n"

        raw += "### 你2024年阅读最多的话题是：\n\n"

        raw += table

        return raw
