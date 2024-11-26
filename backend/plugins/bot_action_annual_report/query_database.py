from ...discourse_api import BotAPI
from fluent_discourse import DiscourseError
import json
from functools import wraps

def format_params(params):
    if params is None:
        return {}
    else:
        for k, v in params.items():
            if isinstance(v, str):
                continue
            elif isinstance(v, bool):
                params[k] = str(v).lower()
            else:
                params[k] = str(v)
        return params
def query_database(api: BotAPI, query_id: int, params=None, query_group="bot"):
    query = format_params(params)
    res = api.client.g[query_group].reports[query_id].run.json.post(
        {"params": json.dumps(query)})
    return res


def query_database_paged(api: BotAPI, query_id: int, params=None, query_group="bot", page_size=500000):
    result = {
        "rows": [],
        "columns": None,
        "duration": 0.0,
        "result_count": 0
    }
    if params is None:
        params = {}
    has_more = True
    retry_times_left = 3
    current_page = 0
    while has_more:
        paged_params = params.copy()
        paged_params['offset'] = current_page * page_size
        query = format_params(paged_params)
        try:
            res = api.client.g[query_group].reports[query_id].run.json.post(
                {"params": json.dumps(query), "limit": page_size})
        except DiscourseError as e:
            if "statement timeout" in e.args[0]:
                retry_times_left -= 1
                if retry_times_left == 0:
                    raise DiscourseError(
                        "Query timeout, max retry times reached, please decrease page_size and try again.")
                else:
                    continue
            else:
                raise
        has_more = len(res["rows"]) == page_size
        if result["columns"] is None:
            result["columns"] = res["columns"]
        else:
            assert result["columns"] == res["columns"], "Columns not match"
        result["rows"].extend(res["rows"])
        result["duration"] += res["duration"]
        result["result_count"] += res["result_count"]
        retry_times_left = 3
        current_page += 1
    return result

def retry_when_timeout(retry_times=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_times_left = retry_times
            while retry_times_left > 0:
                try:
                    return func(*args, **kwargs)
                except DiscourseError as e:
                    if "statement timeout" in e.args[0]:
                        retry_times_left -= 1
                        if retry_times_left == 0:
                            raise DiscourseError(
                                f"Query timeout, max retry times reached, args: {args}, kwargs: {kwargs}")
                    else:
                        raise
        return wrapper
    return decorator
    
