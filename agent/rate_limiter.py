"""Simple rate limiter with optional Redis backing."""

import time
import threading
from typing import Optional

from config import RATE_LIMIT_WINDOW_SECS, RATE_LIMIT_MAX_REQUESTS
from redis_client import redis_client


class RateLimiter:
    def __init__(self):
        self.redis = redis_client
        self.window = RATE_LIMIT_WINDOW_SECS
        self.max_requests = RATE_LIMIT_MAX_REQUESTS
        self.lock = threading.Lock()
        self.counters = {}

    def _get_key(self, client_id: str) -> str:
        return f"javis:rate:{client_id}"

    def is_allowed(self, client_id: str) -> bool:
        key = self._get_key(client_id)
        if self.redis:
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, self.window)
            return count <= self.max_requests

        now = int(time.time())
        with self.lock:
            window_start, count = self.counters.get(client_id, (now, 0))
            if now - window_start >= self.window:
                self.counters[client_id] = (now, 1)
                return True
            if count + 1 > self.max_requests:
                self.counters[client_id] = (window_start, count + 1)
                return False
            self.counters[client_id] = (window_start, count + 1)
            return True
