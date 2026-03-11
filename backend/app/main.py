"""
Application factory — creates and configures the FastAPI app.

Keeping this file small (< 50 lines) is intentional:
  - Routes live in app/api/
  - Config lives in app/core/config.py
  - Exception handlers live in app/core/exceptions.py
"""
import os

from app.core.logger import logger
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.api.v1 import api_v1_router
from app.core.database import close_pool
from contextlib import asynccontextmanager

# ── Project root (two levels above this file's directory: backend/app/main.py → backend/app → backend → root) ───
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_app() -> FastAPI:
    """Create and return the configured FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Startup / shutdown lifecycle hook."""
        logger.info("Application starting up... logs initialized.")
        yield  # app runs here
        # ── Shutdown: release DB pool connections cleanly ──────────────────
        logger.info("Application shutting down...")
        close_pool()

    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="Proposal Automation System — REST API",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # ── API routes ────────────────────────────────────────────────────────────
    app.include_router(api_v1_router)

    # ── Info endpoint ─────────────────────────────────────────────────────────
    @app.get("/api", tags=["Info"])
    def api_info():
        return {
            "message": settings.API_TITLE,
            "version": settings.API_VERSION,
            "docs": "/docs",
        }

    # ── React SPA: Serve the built frontend ─────────────────────────────────
    _react_dist = os.path.join(_ROOT, "frontend", "dist")
    _react_index = os.path.join(_react_dist, "index.html")

    # Mount React build assets (JS/CSS bundles)
    _react_assets = os.path.join(_react_dist, "assets")
    if os.path.isdir(_react_assets):
        app.mount("/assets", StaticFiles(directory=_react_assets), name="react-assets")

    # ── Static files (logos, etc.) ────────────────────────────────────────────
    _static = os.path.join(_ROOT, "static")
    if os.path.isdir(_static):
        app.mount("/static", StaticFiles(directory=_static), name="static")

    # ── Catch-all: serve React index.html for client-side routing ─────────
    @app.get("/{full_path:path}", tags=["UI"])
    def serve_react_spa(full_path: str):
        """Serve the React SPA for all non-API routes."""
        if os.path.isfile(_react_index):
            return FileResponse(_react_index, media_type="text/html")
        # Fallback: return API info if React build not found
        return api_info()

    return app


# Module-level app instance consumed by uvicorn
app = create_app()
