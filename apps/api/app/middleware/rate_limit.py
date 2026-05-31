"""Per-IP token-bucket rate limiting middleware.

Controlled by settings.RATE_LIMIT_ENABLED, RATE_LIMIT_ANON (req/min for
unauthenticated IPs), and RATE_LIMIT_AUTH (req/min for authenticated IPs).
Presence of a valid Authorization header is used as a heuristic to classify
authenticated requests — actual token validation still happens in route deps.
"""

import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


class _Bucket:
    __slots__ = ("tokens", "last_refill")

    def __init__(self, capacity: float) -> None:
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def consume(self, capacity: float, refill_rate: float) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(capacity, self.tokens + elapsed * refill_rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._buckets: dict[str, _Bucket] = defaultdict(lambda: _Bucket(settings.RATE_LIMIT_ANON))
        self._lock = Lock()

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _capacity(self, request: Request) -> float:
        auth = request.headers.get("Authorization", "")
        return float(
            settings.RATE_LIMIT_AUTH if auth.lower().startswith("bearer ") else settings.RATE_LIMIT_ANON
        )

    async def dispatch(self, request: Request, call_next: object) -> Response:
        ip = self._client_ip(request)
        capacity = self._capacity(request)
        refill_rate = capacity / 60.0  # tokens per second

        with self._lock:
            bucket = self._buckets[ip]
            allowed = bucket.consume(capacity, refill_rate)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)  # type: ignore[operator]
