"""FastAPI application factory"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.modules.audit.router import get_audit_router
from app.modules.auth.router import get_auth_router
from app.modules.chat.router import get_chat_router
from app.modules.nanos.router import get_nanos_router
from app.modules.search.router import get_search_router
from app.modules.upload.router import get_upload_router
from app.monitoring import configure_monitoring
from app.redis_client import check_redis_health, close_redis, get_redis
from app.security.middleware import TLSRedirectMiddleware, parse_csv_values

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup and shutdown)"""
    # Startup: Initialize Redis connection
    await get_redis()
    yield
    # Shutdown: Close Redis connection
    await close_redis()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Add CORS middleware with configurable origins for production deployment
    default_cors_origins = [
        "http://localhost:3000",  # Docker frontend
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    # Load from CORS_ORIGINS environment variable if set (comma-separated)
    cors_origins_env = os.getenv("CORS_ORIGINS")
    if cors_origins_env:
        cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
    else:
        cors_origins = default_cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    enforce_tls = settings.SECURITY_ENFORCE_TLS or settings.ENV == "production"
    if settings.SECURITY_TLS_REDIRECT_INSECURE:
        app.add_middleware(
            TLSRedirectMiddleware,
            enabled=enforce_tls,
            protected_path_prefixes=parse_csv_values(settings.SECURITY_TLS_PROTECTED_PATHS),
            trusted_proxies=set(parse_csv_values(settings.SECURITY_TRUSTED_PROXIES)),
            allowed_hosts=frozenset(parse_csv_values(settings.SECURITY_ALLOWED_HOSTS)),
        )

    # Include routers
    app.include_router(get_auth_router())
    app.include_router(get_audit_router())
    app.include_router(get_upload_router())
    app.include_router(get_nanos_router())
    app.include_router(get_search_router())
    app.include_router(get_chat_router())
    configure_monitoring(app)

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint with Redis status."""
        redis_healthy = await check_redis_health()
        return {
            "status": "ok" if redis_healthy else "degraded",
            "version": settings.APP_VERSION,
            "services": {
                "redis": "up" if redis_healthy else "down",
            },
        }

    @app.get("/")
    async def root() -> RedirectResponse:
        """Redirect root to frontend landing page"""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=frontend_url, status_code=307)

    return app


app = create_app()
