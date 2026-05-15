"""
Request Logger Middleware — Structured logging for every request.
Gives you latency, status, path on every call.
In production: pipe to Datadog / Grafana / CloudWatch.
"""

import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        t0 = time.monotonic()
        response = await call_next(request)
        elapsed_ms = round((time.monotonic() - t0) * 1000)

        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} | {elapsed_ms}ms"
        )

        # Add latency header (useful for debugging)
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        return response