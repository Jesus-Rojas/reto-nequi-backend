import time
from collections import defaultdict

from fastapi.responses import JSONResponse
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.schemas.message import ErrorDetail, ErrorResponse


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding-window rate limiter (per client IP)."""

    _EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self._limit = requests_per_minute
        self._windows: dict[str, list[float]] = defaultdict(list)

    def _evict_expired_timestamps(self, timestamps: list[float], window_start: float) -> list[float]:
        return [timestamp for timestamp in timestamps if timestamp > window_start]

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - 60.0

        self._windows[client_ip] = self._evict_expired_timestamps(self._windows[client_ip], window_start)

        if len(self._windows[client_ip]) >= self._limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="RATE_LIMIT_EXCEEDED",
                        message="Demasiadas solicitudes",
                        details="Límite de solicitudes excedido. Intenta de nuevo en un minuto.",
                    )
                ).model_dump(),
            )

        self._windows[client_ip].append(now)
        return await call_next(request)
