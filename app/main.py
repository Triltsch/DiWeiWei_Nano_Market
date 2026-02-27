"""FastAPI application factory"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.modules.auth.router import get_auth_router

settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(get_auth_router())

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
