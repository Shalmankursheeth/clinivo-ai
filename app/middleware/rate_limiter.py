"""
Rate Limiter Middleware — Redis sliding window

WHY THIS EXISTS:
  Without rate limiting, a single caller hammering the endpoint can:
  - Burn Groq/ElevenLabs API quota
  - Cause Twilio webhook timeouts
  - Degrade all other callers

  Per-IP sliding window using Redis INCR + EXPIRE.
  Redis makes it work across multiple instances (unlike in-memory rate limiting).
"""

import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis_client import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.limit = calls_per_minute

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check and static files
        if request.url.path in ("/", "/docs", "/redoc") or request.url.path.startswith("/audio"):
            return await call_next(request)

        # Identifier: IP or Twilio CallSid (more accurate for voice calls)
        identifier = request.headers.get("X-Forwarded-For") or request.client.host

        allowed = await redis_client.check_rate_limit(
            identifier=identifier,
            limit=self.limit,
            window_seconds=60
        )

        if not allowed:
            logger.warning(f"Rate limit exceeded: {identifier}")
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"}
            )

        return await call_next(request)