"""Middlewares for the Janus inference service."""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LatencyLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request along with its duration."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        start = time.monotonic()
        response = await call_next(request)
        elapsed = time.monotonic() - start
        logger.info(
            "%s %s → %s  (%.2fs)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        response.headers["X-Processing-Time-MS"] = str(round(elapsed * 1000, 1))
        return response


def register_middleware(app: FastAPI) -> None:
    """Attach all common middlewares to *app*."""
    app.add_middleware(LatencyLoggingMiddleware)
