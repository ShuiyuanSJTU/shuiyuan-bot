import redis
from typing import Callable, Optional, Union
from functools import wraps
from ..bot_config import config as Config
import logging
import json


class RedisClient:
    _instance = None

    def __new__(cls, host: str = 'localhost', port: int = 6379, db: int = 0):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._client = redis.Redis(host=host, port=port, db=db)
        return cls._instance

    @property
    def client(self):
        return self._client


global _redis_client, _redis_available

try:
    _redis_client: redis.Redis = RedisClient(
        host=Config.redis_host,
        port=Config.redis_port
    ).client
    _redis_client.ping()
    _redis_available = True
except Exception as e:
    logging.warning(f"Failed to connect to Redis: {str(e)}")
    _redis_client = None
    _redis_available = False


def redis_cache(cache_key: Optional[Union[str, Callable]] = None, ex: int = 3600):
    if not _redis_available:
        return lambda f: f

    def decorator(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if cache_key is None:
                _cache_key = f"{f.__module__}.{f.__name__}-{args}-{kwargs}"
            elif callable(cache_key):
                _cache_key = cache_key(*args, **kwargs)
            else:
                _cache_key = cache_key

            cache = _redis_client.get(_cache_key)

            if cache is not None:
                return json.loads(cache.decode())
            else:
                try:
                    res = f(*args, **kwargs)
                except Exception:
                    raise
                if _cache_key is not None:
                    try:
                        _redis_client.set(_cache_key, json.dumps(res), ex=ex)
                    except Exception as e:
                        logging.warning(
                            f"Failed to set cache for key {_cache_key}: {str(e)}")
            return res
        return wrapper
    return decorator
