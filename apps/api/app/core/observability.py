"""Request IDs, structured access logs, in-process metrics and rate limiting."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("unios.access")


@dataclass
class Metrics:
    started_at: float = field(default_factory=time.time)
    requests_total: int = 0
    errors_total: int = 0
    rate_limited_total: int = 0
    latency_ms_total: float = 0.0
    by_path: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _lock: Lock = field(default_factory=Lock)

    def observe(self, path: str, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self.requests_total += 1
            self.latency_ms_total += duration_ms
            self.by_path[path] += 1
            if status_code >= 500:
                self.errors_total += 1
            if status_code == 429:
                self.rate_limited_total += 1

    def snapshot(self) -> dict:
        with self._lock:
            average = self.latency_ms_total / self.requests_total if self.requests_total else 0.0
            top = sorted(self.by_path.items(), key=lambda item: item[1], reverse=True)[:15]
            return {
                "uptime_seconds": round(time.time() - self.started_at, 1),
                "requests_total": self.requests_total,
                "errors_total": self.errors_total,
                "rate_limited_total": self.rate_limited_total,
                "average_latency_ms": round(average, 2),
                "top_paths": [{"path": path, "count": count} for path, count in top],
            }


metrics = Metrics()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attaches a request id, logs one structured line and records metrics."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        path = request.scope.get("route").path if request.scope.get("route") else request.url.path
        metrics.observe(path, response.status_code, duration_ms)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s %s %.1fms request_id=%s",
            request.method,
            path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= limit:
                return False, int(window - (now - bucket[0])) + 1
            bucket.append(now)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()

_AI_PREFIXES = ("/api/v1/chat", "/api/v1/tools", "/api/v1/documents", "/api/v1/multimodal")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-client sliding window. AI routes get a tighter budget than the rest.

    In-process by design: it protects a single API instance. For a multi-instance
    deployment, put the shared Redis-backed limiter in front (see docs/deployment.md).
    """

    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled or request.method == "OPTIONS":
            return await call_next(request)

        client = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        client = client or (request.client.host if request.client else "unknown")
        path = request.url.path
        is_ai = path.startswith(_AI_PREFIXES)
        limit = settings.ai_rate_limit_requests if is_ai else settings.rate_limit_requests
        window = (
            settings.ai_rate_limit_window_seconds if is_ai else settings.rate_limit_window_seconds
        )
        allowed, retry_after = limiter.allow(f"{'ai' if is_ai else 'all'}:{client}", limit, window)
        if not allowed:
            metrics.observe(path, 429, 0.0)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
