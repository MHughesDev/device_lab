"""Auth audit log middleware.

Emits a structured JSON line to stdout for every 401/403 response and for
auth-related routes (login, logout, password-change). Controlled by
settings.AUDIT_LOG_ENABLED.
"""

import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger("audit")

_AUTH_PATHS = {"/login", "/logout", "/password-change", "/reset-password"}


def _is_auth_path(path: str) -> bool:
    return any(segment in path for segment in _AUTH_PATHS)


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        start = time.time()
        response: Response = await call_next(request)  # type: ignore[operator]
        status = response.status_code

        if status in (401, 403) or _is_auth_path(request.url.path):
            record = {
                "event": "auth",
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "ip": (request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "unknown")),
                "duration_ms": round((time.time() - start) * 1000),
            }
            print(json.dumps(record), flush=True)

        return response
