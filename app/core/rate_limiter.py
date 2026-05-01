import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding-window rate limiter (per client IP)."""

    _EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self._limit = requests_per_minute
        self._windows: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - 60.0

        # Evict timestamps outside the current window
        self._windows[client_ip] = [
            t for t in self._windows[client_ip] if t > window_start
        ]

        if len(self._windows[client_ip]) >= self._limit:
            return Response(
                content=(
                    '{"status":"error","error":{'
                    '"code":"RATE_LIMIT_EXCEEDED",'
                    '"message":"Demasiadas solicitudes",'
                    '"details":"Límite de solicitudes excedido. Intenta de nuevo en un minuto."}}'
                ),
                status_code=429,
                media_type="application/json",
            )

        self._windows[client_ip].append(now)
        return await call_next(request)
