from datetime import timedelta, datetime
import os
import pickle
import logging
import numpy as np
import pandas as pd

from .base_bot_report_action import BaseBotReportAction, ReportOptions
from .query_database import query_database, query_database_paged
from .report_plot import plot_post_activity_hour, plot_post_activity_year
from .preprocess_data import preprocess_posts_data

from ...utils.redis_cache import redis_cache
from ...model import Post

logger = logging.getLogger(__name__)

CURRENT_YEAR = 2024


class BotPostReport(BaseBotReportAction):
    action_name = "BotPostReport"
    trigger_keyword = "我的2024发帖报告"

    def __init__(self) -> None:
        super().__init__()
        if self.enabled:
            self.load_global_report_data()

    def load_global_report_data(self):
        processed_data_path = os.path.join(
            self.config.working_path, "post_report_processed.pkl")
        if not os.path.exists(processed_data_path):
            logger.info("Processed data not found, querying database...")
            raw_data = query_database_paged(self.api, self.config.user_post_query_id, {
            }, self.config.query_group, page_size=500000)
            logger.info("Query finished, preprocessing data...")
            preprocess_posts_data(raw_data, processed_data_path)

        with open(processed_data_path, "rb") as f:
            # post_count, post_read_count, post_character_count,post_count_rank,
            # post_read_count_rank, post_character_count_rank,
            # post_days, post_days_rank
            self.user_table: pd.DataFrame = pickle.load(f)

            # dict: user_id: np.darray[365]
            self.user_post_day_count = pickle.load(f)
            # dict: user_id: np.darray[24]
            self.user_post_hour_count = pickle.load(f)

        self.all_user_count = self.api.client.about.json.get()[
            "about"]["stats"]["users_count"]

    def get_post_data(self, user_id):
        user_post_day_count = self.user_post_day_count.get(user_id, None)
        user_post_hour_count = self.user_post_hour_count.get(user_id, None)
        try:
            user_table_row = self.user_table.loc[user_id]
        except KeyError:
            user_table_row = None
        if user_post_day_count is None or user_post_hour_count is None or user_table_row is None:
            return None
        else:
            return user_post_day_count, user_post_hour_count, user_table_row

    def get_post_tag_data(self, user_id):
        try:
            # res = query_database(self.api, 74, {"user_id":user_id}, self.cache_key(user_id, 74))
            res = query_database(self.api, self.config.post_tag_query_id, {
                                 "user_id": user_id}, self.config.query_group)
        except Exception as e:
            res = None
            print(e)
        else:
            return res

    @staticmethod
    def get_most_active_hour_period(hour_count, window_size=6):
        most_active = np.argmax(np.convolve(
            np.tile(hour_count, 3), np.ones(window_size), 'same')[24:48])
        left = most_active - window_size//2
        right = most_active + (window_size-1)//2
        return left, right

    @staticmethod
    def get_activity_per_weekday(post_day):
        offset = datetime(CURRENT_YEAR, 1, 1).weekday()
        activity = np.zeros(7*53)
        activity[offset:offset + len(post_day)] = post_day
        activity_matrix = np.reshape(activity, (-1, 7)).T
        activity_per_weekday = np.sum(activity_matrix, axis=1).astype(np.int32)
        return activity_per_weekday

    def render_post_count_activity(self, user_post_day_count, user_post_hour_count, user_table_row):
        raw = ''

        post_count = user_table_row['post_count']
        post_count_rank = user_table_row['post_count_rank']

        raw += f"你2024年在水源创建了{post_count:.0f}条帖子，"
        if post_count_rank < 100:
            raw += f"在所有用户中排名第{post_count_rank:.0f}！"
        else:
            raw += f"超过了{int((1 - (post_count_rank-1)/self.all_user_count)*1000)/10:.1f}%的用户"
        raw += "\n\n"

        post_character_count = user_table_row['post_character_count']
        post_character_count_rank = user_table_row['post_character_count_rank']

        raw += f"这些帖子共有{post_character_count:.0f}个字，"
        if post_character_count_rank < 100:
            raw += f"在所有用户中排名第{post_character_count_rank:.0f}！"
        else:
            raw += f"超过了{int((1 - (post_character_count_rank-1)/self.all_user_count)*1000)/10:.1f}%的用户"
        raw += "\n\n"

        post_read_count = user_table_row['post_read_count']
        post_read_count_rank = user_table_row['post_read_count_rank']
        if post_read_count > 10:
            raw += f"这些帖子共有{post_read_count:.0f}次阅读，"
            if post_read_count_rank < 100:
                raw += f"在所有用户中排名第{post_read_count_rank:.0f}！"
            else:
                raw += f"超过了{int((1 - (post_read_count_rank-1)/self.all_user_count)*1000)/10:.1f}%的用户"
            raw += "\n\n"

        return raw

    def render_post_day_count_activity(self, user_post_day_count, user_post_hour_count, user_table_row):
        raw = ''

        days_posted = user_table_row['post_days']
        if days_posted >= 361:
            raw += "你2024年一天不落地在水源发帖，每日打卡！\n\n"
        elif days_posted > 0:
            post_days_percentage = int(
                (1 - (user_table_row['post_days_rank']-1)/self.all_user_count)*1000)/10
            raw += f"你2024年共在水源发帖{days_posted:.0f}天，超过了{post_days_percentage:.1f}%的用户"
            if days_posted < 30:
                raw += "，或许可以多在水源发发帖，和大家多多交流呢？\n\n"
            else:
                raw += "\n\n"

        most_post_day_of_year = int(user_post_day_count.argmax())
        if user_post_day_count[most_post_day_of_year] > 10:
            most_post_day_of_year_datetime = datetime(
                CURRENT_YEAR, 1, 1) + timedelta(days=most_post_day_of_year)
            raw += f"你2024年在水源发帖最多的一天是{most_post_day_of_year_datetime.month}月{most_post_day_of_year_datetime.day}日，共发了{user_post_day_count[most_post_day_of_year]:.0f}条帖子，还记得那一天发生了什么吗？\n\n"

        post_weekday_count = self.get_activity_per_weekday(user_post_day_count)
        most_post_weekday = post_weekday_count.argmax()
        if post_weekday_count[most_post_weekday] > 100:
            weekday_chinese = ['一', '二', '三', '四', '五', '六', '日']
            raw += f"你最喜欢在星期{weekday_chinese[most_post_weekday]}发帖，每周这一天发出的帖子占了全年发帖总量的{post_weekday_count[most_post_weekday]/user_table_row['post_count']:.1%}"
            if post_weekday_count[most_post_weekday]/user_table_row['post_count'] >= 0.2:
                raw += "，是不是有什么特别的原因呢？\n\n"
            else:
                raw += "\n\n"

        if days_posted > 10:
            fig = plot_post_activity_year(user_post_day_count)
            upload_meta = self.api.create_upload(fig, "post_activity_year.png")
            fig_short_url = upload_meta['short_url']
            raw += f"![post_activity_year]({fig_short_url})\n\n"

        return raw

    def render_post_hour_count_activity(self, user_post_day_count, user_post_hour_count, user_table_row):
        raw = ''

        most_active_hour_period = self.get_most_active_hour_period(
            user_post_hour_count, window_size=6)
        most_post_hour_of_day = user_post_hour_count.argmax()

        if user_table_row['post_count'] > 10:
            raw += f"你最喜欢在{most_active_hour_period[0]%24}点至{most_active_hour_period[1]%24}点发帖"
            if user_post_hour_count[most_post_hour_of_day] > 10:
                # check if most active hour is in most active hour period
                if most_active_hour_period[0] <= most_post_hour_of_day <= most_active_hour_period[1]\
                        or most_active_hour_period[0] <= most_post_hour_of_day + 24 <= most_active_hour_period[1]\
                        or most_active_hour_period[0] <= most_post_hour_of_day - 24 <= most_active_hour_period[1]:
                    raw += f"，其中{most_post_hour_of_day}点是你最常发帖的一个小时\n\n"
                else:
                    raw += f"，但要说到你最常发帖的一个小时，却是{most_post_hour_of_day}点，你有{user_post_hour_count[most_post_hour_of_day]:.0f}个帖子是在每天的这个小时发出的\n\n"
            else:
                raw += "\n\n"

        if user_table_row['post_count'] > 10:
            fig = plot_post_activity_hour(user_post_hour_count)
            upload_meta = self.api.create_upload(fig, "post_activity_hour.png")
            fig_short_url = upload_meta['short_url']
            raw += f"![post_activity_hour]({fig_short_url})\n\n"

        return raw

    def render_post_tag_activity(self, user_id):
        raw = ''

        data = self.get_post_tag_data(user_id)
        if data is None:
            return '暂时无法获取你最常使用的标签数据，请稍后重试'

        tags = data['rows']
        if len(tags) == 0:
            return raw

        raw += "你最喜欢在这些标签下回复：\n\n"

        for tag in tags:
            if tag[0] in ('水印',):
                continue
            raw += f"#{tag[0]} "

        raw += "\n\n"

        return raw

    @redis_cache(ex=600, cache_key=BaseBotReportAction.cache_key_for_main_content)
    def get_reply_main_content(self, user_id: int, post: Post, opts: ReportOptions):
        raw = ''

        user_post_day_count, user_post_hour_count, user_table_row = self.get_post_data(
            user_id)

        raw += self.render_post_count_activity(
            user_post_day_count, user_post_hour_count, user_table_row)
        raw += self.render_post_day_count_activity(
            user_post_day_count, user_post_hour_count, user_table_row)
        raw += self.render_post_hour_count_activity(
            user_post_day_count, user_post_hour_count, user_table_row)
        raw += self.render_post_tag_activity(user_id)

        return raw
