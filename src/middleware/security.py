"""Security middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def configure_security(app: FastAPI, enable_cors: bool = True) -> None:
    """
    Configure security middleware for the application.

    Args:
        app: FastAPI application instance
        enable_cors: Whether to enable CORS
    """
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Reset"],
        )


def get_security_headers() -> dict:
    """Get recommended security headers."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Cache-Control": "no-store, no-cache, must-revalidate",
    }
