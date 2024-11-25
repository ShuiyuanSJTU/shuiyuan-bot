from collections import defaultdict
import pandas as pd
import numpy as np
import pytz
import re
import os
import pickle
from datetime import datetime


def preprocess_posts_data(data: dict, path: str):
    # colums: id user raw created_at reads
    raw_rows = data['rows']
    columns = data['columns']
    data_table = pd.DataFrame(raw_rows, columns=columns)
    data_table['created_at'] = data_table['created_at'].map(
        lambda x: datetime.fromtimestamp(x, pytz.timezone('Asia/Shanghai')))
    data_table.set_index('id', inplace=True)
    user_post_count = defaultdict(lambda: 0)
    user_post_character_count = defaultdict(lambda: 0)
    user_post_read_count = defaultdict(lambda: 0)
    user_post_hour_count = defaultdict(lambda: np.zeros(24, dtype=np.int32))
    user_post_day_count = defaultdict(lambda: np.zeros(365, dtype=np.int32))
    for row in data_table.itertuples():
        user_id = row.user_id
        user_post_count[user_id] += 1
        user_post_read_count[user_id] += row.reads
        user_post_character_count[user_id] += len(
            re.findall(r'[\u4e00-\u9fa5]', row.raw))
        user_post_hour_count[user_id][row.created_at.hour] += 1
        day_of_year = row.created_at.timetuple().tm_yday - 1
        user_post_day_count[user_id][day_of_year] += 1
    user_post_days = {
        user_id: np.count_nonzero(user_post_day_count[user_id])
        for user_id in user_post_day_count
    }
    user_table = pd.DataFrame(
        columns=['user_id', 'post_count', 'post_read_count', 'post_character_count'])
    user_table.set_index('user_id', inplace=True)

    user_table['post_count'] = pd.Series(
        user_post_count, copy=True).astype(np.int32)
    user_table['post_read_count'] = pd.Series(
        user_post_read_count, copy=True).astype(np.int32)
    user_table['post_character_count'] = pd.Series(
        user_post_character_count, copy=True).astype(np.int32)
    user_table['post_count_rank'] = user_table['post_count'].rank(
        ascending=False)
    user_table['post_read_count_rank'] = user_table['post_read_count'].rank(
        ascending=False)
    user_table['post_character_count_rank'] = user_table['post_character_count'].rank(
        ascending=False)
    user_table['post_days'] = pd.Series(
        user_post_days, copy=True).astype(np.int32)
    user_table['post_days_rank'] = user_table['post_days'].rank(
        ascending=False)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(user_table, f)
        pickle.dump(dict(user_post_day_count), f)
        pickle.dump(dict(user_post_hour_count), f)


def preprocess_visit_data(data: dict, path: str):
    table = pd.DataFrame(data['rows'], columns=data['columns'])
    table.set_index('user_id', inplace=True)
    table['posts_read_rank'] = table['posts_read'].rank(
        method='min', ascending=False)
    table['time_read_rank'] = table['time_read'].rank(
        method='min', ascending=False)
    table['days_visited_rank'] = table['days_visited'].rank(
        method='min', ascending=False)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(table, f)
