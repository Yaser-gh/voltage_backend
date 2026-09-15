"""
Application entrypoint: FastAPI app factory, middleware, routers, and lifecycle hooks.

Run with:  uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.config.settings import settings
from app.core.limiter import limiter
from app.core.logging import configure_logging, get_logger
from app.database.session import dispose_engine
from app.dependencies.redis import dispose_redis_pool
from app.exceptions.handlers import register_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_time import RequestTimeMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

configure_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle — connection pools, background jobs, etc."""
    logger.info("application_startup", environment=settings.ENVIRONMENT)
    yield
    logger.info("application_shutdown")
    await dispose_engine()
    await dispose_redis_pool()


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-ready backend API for managing electrical installation projects: "
            "users, projects, payments, and file attachments, with full JWT authentication, "
            "role/permission-based authorization, and hardened security controls."
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state
    # --------------------------------------------------------------- Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --------------------------------------------------------------- CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # --------------------------------------------------------------- Custom middleware
    # NOTE: Starlette applies middleware in reverse order of addition (last added runs first).
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestTimeMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # --------------------------------------------------------------- Exception handlers
    register_exception_handlers(app)

    # --------------------------------------------------------------- Routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["Health"], summary="Liveness/readiness probe", status_code=status.HTTP_200_OK)
    async def health_check() -> dict:
        """Simple health-check endpoint for load balancers / container orchestrators."""
        return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}

    return app


app = create_app()
