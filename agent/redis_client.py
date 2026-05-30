"""Redis helper for optional caching and rate limiting."""

import os
import redis
from config import REDIS_URL, ENABLE_REDIS_CACHE

redis_client = None
if ENABLE_REDIS_CACHE:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print(f"[JAVIS-Redis] Connected to Redis at {REDIS_URL}")
    except Exception as e:
        print(f"[JAVIS-Redis] Redis unavailable: {e}")
        redis_client = None
