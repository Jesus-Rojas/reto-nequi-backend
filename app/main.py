from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.messages import router as messages_router
from app.config import get_settings
from app.core.error_handlers import (
    internal_server_error_handler,
    message_api_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import MessageAPIException
from app.core.rate_limiter import RateLimiterMiddleware
from app.database import Base, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (idempotent)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API RESTful para procesamiento de mensajes de chat. "
        "Incluye validación, filtro de contenido, paginación, "
        "búsqueda y actualizaciones en tiempo real vía WebSocket."
    ),
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    RateLimiterMiddleware,
    requests_per_minute=settings.rate_limit_per_minute,
)

# ── Exception handlers ────────────────────────────────────────────────────────

app.add_exception_handler(MessageAPIException, message_api_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, internal_server_error_handler)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(messages_router)


# ── Utility endpoints ─────────────────────────────────────────────────────────

@app.get("/health", tags=["health"], summary="Health check")
def health_check():
    return {"status": "ok", "version": settings.app_version}
