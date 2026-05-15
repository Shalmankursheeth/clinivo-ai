"""
Redis Client
Replaces in-memory session dict → distributed, persistent, multi-instance safe.

WHY THIS MATTERS:
  In-memory sessions break under:
  - multi-instance deployment (sessions on instance A invisible to instance B)
  - process restart (all sessions lost mid-call)
  - horizontal scaling (load balancer routes same caller to different instance)

  Redis solves all three. Sessions are external to the process.
"""

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def connect(self):
        self._client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        await self._client.ping()
        logger.info(f"Redis connected: {settings.REDIS_URL}")

    async def disconnect(self):
        if self._client:
            await self._client.aclose()

    async def ping(self) -> bool:
        try:
            return await self._client.ping()
        except Exception:
            return False

    # ── Session ops ───────────────────────────────────────────────────────────

    async def get_session(self, phone: str) -> dict:
        """Get caller session. Returns default if not exists."""
        key = f"session:{phone}"
        raw = await self._client.get(key)
        if raw:
            return json.loads(raw)
        return {
            "state": "active",
            "data": {
                "doctor": None,
                "speciality": None,
                "date": None,
                "time_preference": None,
                "last_intent": None,
                "need_alternative": False
            }
        }

    async def save_session(self, phone: str, session: dict):
        """Save session with TTL. Auto-expires idle sessions."""
        key = f"session:{phone}"
        await self._client.setex(
            key,
            settings.SESSION_TTL_SECONDS,
            json.dumps(session)
        )

    async def delete_session(self, phone: str):
        """Called when call ends."""
        key = f"session:{phone}"
        await self._client.delete(key)
        logger.info(f"Session deleted: {phone}")

    # ── TTS cache ops ─────────────────────────────────────────────────────────

    async def get_tts_cache(self, text_hash: str) -> Optional[bytes]:
        """Check if TTS audio is cached."""
        key = f"tts:{text_hash}"
        return await self._client.get(key)

    async def set_tts_cache(self, text_hash: str, audio_url: str, ttl: int = 86400):
        """Cache TTS audio URL for 24h."""
        key = f"tts:{text_hash}"
        await self._client.setex(key, ttl, audio_url)

    # ── Rate limiting ops ─────────────────────────────────────────────────────

    async def check_rate_limit(self, identifier: str, limit: int, window_seconds: int = 60) -> bool:
        """
        Sliding window rate limiter.
        Returns True if request is allowed, False if rate limited.
        """
        key = f"rate:{identifier}"
        pipe = self._client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()
        current_count = results[0]
        return current_count <= limit

    # ── General ops ───────────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[str]:
        return await self._client.get(key)

    async def set(self, key: str, value: Any, ttl: int = None):
        if ttl:
            await self._client.setex(key, ttl, str(value))
        else:
            await self._client.set(key, str(value))

    async def delete(self, key: str):
        await self._client.delete(key)


# Singleton
redis_client = RedisClient()