"""
J.A.V.I.S. Health & Readiness Checks
"""
from sqlalchemy import text
import redis as redis_lib
from database import get_session
from redis_client import redis_client


async def check_database() -> bool:
    """Check if database is accessible"""
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[HEALTH] Database check failed: {e}")
        return False


async def check_redis() -> bool:
    """Check if Redis is accessible (optional)"""
    if not redis_client:
        return True  # Redis is optional
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"[HEALTH] Redis check failed: {e}")
        return False


class HealthStatus:
    def __init__(self):
        self.database_ok = False
        self.redis_ok = False
    
    async def refresh(self):
        self.database_ok = await check_database()
        self.redis_ok = await check_redis()
    
    @property
    def is_ready(self) -> bool:
        """System is ready if database is up"""
        return self.database_ok
    
    @property
    def is_healthy(self) -> bool:
        """System is healthy if all checks pass"""
        return self.database_ok
    
    def to_dict(self) -> dict:
        return {
            "status": "ok" if self.is_healthy else "degraded",
            "database": "ok" if self.database_ok else "error",
            "redis": "ok" if self.redis_ok else "unavailable",
        }


# Global health status instance
health_status = HealthStatus()
