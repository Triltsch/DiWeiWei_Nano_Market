"""FastAPI application factory"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.modules.audit.router import get_audit_router
from app.modules.auth.router import get_auth_router
from app.modules.nanos.router import get_nanos_router
from app.modules.upload.router import get_upload_router
from app.redis_client import close_redis, get_redis

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

    # Include routers
    app.include_router(get_auth_router())
    app.include_router(get_audit_router())
    app.include_router(get_upload_router())
    app.include_router(get_nanos_router())

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint"""
        return {"status": "ok", "version": settings.APP_VERSION}

    @app.get("/")
    async def root() -> dict:
        """Root endpoint"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return app


app = create_app()
