"""API module for REST endpoints."""

from src.api.routes import router as api_router
from src.api.health import router as health_router

__all__ = ["api_router", "health_router"]
