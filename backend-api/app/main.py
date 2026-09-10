"""
SafeSkin AI – FastAPI Application Entry Point

Initialises the application, registers all routers, configures CORS,
sets up logging, and loads AI models on startup.
"""

from __future__ import annotations

import logging
import traceback
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.services.ai_pipeline import load_models

# ── Import routers ────────────────────────────────────────────────────
from app.routes import admin, progress, screening, upload, user

# ── Logging setup ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if not get_settings().is_production else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ======================================================================
# Lifespan – startup / shutdown events
# ======================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load AI models on startup; clean up on shutdown."""
    logger.info("SafeSkin AI backend starting up…")
    try:
        load_models()
        logger.info("AI models loaded successfully.")
    except Exception as exc:
        logger.error("Model loading failed (API will use mock mode): %s", exc)
    yield
    logger.info("SafeSkin AI backend shutting down.")


# ======================================================================
# App factory
# ======================================================================

settings = get_settings()

app = FastAPI(
    title="SafeSkin AI API",
    description=(
        "REST API for SafeSkin AI – an AI-powered skin screening assistant. "
        "Provides image quality analysis, dermatological condition screening, "
        "progress tracking, and user management."
    ),
    version="2.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)


# ======================================================================
# Middleware
# ======================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================================================================
# Global exception handler
# ======================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions.
    In production, hides internal details; in development, shows the traceback.
    """
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url, exc)
    body: Dict[str, Any] = {
        "detail": "An internal server error occurred. Please try again later.",
        "path": str(request.url),
    }
    if not settings.is_production:
        body["debug"] = traceback.format_exc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=body,
    )


# ======================================================================
# Core endpoints
# ======================================================================

@app.get("/", tags=["Root"], summary="API information")
async def root() -> Dict[str, Any]:
    """Return basic API metadata."""
    return {
        "name": "SafeSkin AI API",
        "version": "2.0.0",
        "status": "running",
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> Dict[str, str]:
    """
    Lightweight health probe used by load balancers and container orchestrators.
    Returns HTTP 200 when the service is alive.
    """
    return {"status": "healthy", "service": "safeskin-ai-api"}


# ======================================================================
# Router registration
# ======================================================================

app.include_router(upload.router, prefix="/api/v1")
app.include_router(screening.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
