import redis
import json
from datetime import timedelta
import os

if os.getenv("REDIS_HOST", None) is not None:
    r = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT", "6379"), db=int(
        os.getenv("REDIS_DB", "0")), password=os.getenv("REDIS_PASSWORD"))
_local_cache = {}


def get(key: str) -> dict:
    val = None
    try:
        cached_value = r.get(key)
        val = json.loads(cached_value)
    except Exception as e:
        val = _local_cache.get(key)
        if val is not None:
            val = json.loads(val)
    return val


def set(key: str, val: dict):
    data = json.dumps(val)
    try:
        r.set(key, data, ex=timedelta(weeks=1))
    except Exception as e:
        pass
    _local_cache[key] = data
