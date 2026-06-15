from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

CORRELATION_HEADER = "x-request-id"
RESPONSE_TIME_HEADER = "x-response-time-ms"


def _new_correlation_id() -> str:
    return f"req-{uuid.uuid4().hex[:8]}"


def _normalize_correlation_id(raw: str | None) -> str:
    if not raw:
        return _new_correlation_id()
    raw = raw.strip()
    if not raw or len(raw) > 128:
        return _new_correlation_id()
    safe = "".join(ch for ch in raw if ch.isalnum() or ch in "-_.")
    if not safe:
        return _new_correlation_id()
    if not safe.lower().startswith("req-"):
        safe = f"req-{safe[:24]}"
    return safe[:64]


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()

        incoming = request.headers.get(CORRELATION_HEADER)
        correlation_id = _normalize_correlation_id(incoming)

        bind_contextvars(correlation_id=correlation_id)

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            bind_contextvars(latency_ms=int(duration_ms), status="error")
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers[CORRELATION_HEADER] = correlation_id
        response.headers[RESPONSE_TIME_HEADER] = f"{duration_ms:.1f}"
        return response
