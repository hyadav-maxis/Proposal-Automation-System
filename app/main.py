"""
Application factory — creates and configures the FastAPI app.

Keeping this file small (< 50 lines) is intentional:
  - Routes live in app/api/
  - Config lives in app/core/config.py
  - Exception handlers live in app/core/exceptions.py
"""

import os

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

# ── Project root (one level above this file's directory) ─────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app() -> FastAPI:
    """Create and return the configured FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Startup / shutdown lifecycle hook."""
        yield  # app runs here
        # ── Shutdown: release DB pool connections cleanly ──────────────────
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

    # ── Frontend HTML pages ───────────────────────────────────────────────────
    _frontend = os.path.join(_ROOT, "frontend")

    @app.get("/", tags=["UI"])
    def serve_ui():
        """Serve the main proposal UI."""
        p = os.path.join(_frontend, "index.html")
        return FileResponse(p, media_type="text/html") if os.path.isfile(p) else api_info()

    @app.get("/pricing-config", tags=["UI"])
    def serve_pricing_config():
        """Serve the pricing configuration UI."""
        p = os.path.join(_frontend, "pricing_config.html")
        if os.path.isfile(p):
            return FileResponse(p, media_type="text/html")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pricing config page not found")

    @app.get("/chat", tags=["UI"])
    def serve_chat():
        """Serve the AI chat UI."""
        p = os.path.join(_frontend, "chat.html")
        if os.path.isfile(p):
            return FileResponse(p, media_type="text/html")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Chat page not found")

    @app.get("/settings", tags=["UI"])
    def serve_settings():
        """Serve the settings UI."""
        p = os.path.join(_frontend, "settings.html")
        if os.path.isfile(p):
            return FileResponse(p, media_type="text/html")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Settings page not found")

    @app.get("/proposals", tags=["UI"])
    def serve_proposals():
        """Serve the Proposal Management UI."""
        p = os.path.join(_frontend, "proposals.html")
        if os.path.isfile(p):
            return FileResponse(p, media_type="text/html")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Proposals page not found")

    # ── Static files (logos, etc.) — mount LAST so routes take precedence ─────
    _static = os.path.join(_ROOT, "static")
    if os.path.isdir(_static):
        app.mount("/static", StaticFiles(directory=_static), name="static")

    return app


# Module-level app instance consumed by uvicorn
app = create_app()
