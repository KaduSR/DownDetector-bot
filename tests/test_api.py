"""Tests for REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from src.models import OutageReport, StatusEnum, SeverityEnum


# Note: These tests use a mock setup since the actual app requires
# scheduler initialization. In production, you'd use proper fixtures.

class TestAPIEndpoints:
    """Tests for API endpoints."""

    def test_health_endpoint_structure(self):
        """Test health endpoint response structure."""
        # This is a structural test - actual integration tests
        # would require the full app setup
        expected_fields = ["status", "timestamp", "version", "uptime_seconds"]
        # Verify model has all fields
        from src.models import HealthCheckResponse
        assert all(field in HealthCheckResponse.model_fields for field in expected_fields)

    def test_status_response_model(self):
        """Test status response model."""
        from src.models import StatusResponse

        response = StatusResponse(
            services=[],
            total_count=0,
            timestamp=datetime.now(),
        )
        assert response.total_count == 0
        assert response.services == []

    def test_changes_response_model(self):
        """Test changes response model."""
        from src.models import ChangesResponse

        response = ChangesResponse(
            changes=[],
            total_count=0,
            time_range={"start": "2024-01-01", "end": "2024-01-02"},
        )
        assert response.total_count == 0

    def test_error_response_model(self):
        """Test error response model."""
        from src.models import ErrorResponse

        response = ErrorResponse(
            error={"code": "NOT_FOUND", "message": "Service not found"},
            timestamp=datetime.now(),
        )
        assert response.error["code"] == "NOT_FOUND"


class TestRateLimiter:
    """Tests for rate limiter."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        from src.middleware.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=100)
        assert limiter.requests_per_minute == 100

    def test_rate_limiter_remaining(self):
        """Test getting remaining requests."""
        from src.middleware.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=100)
        remaining = limiter.get_remaining("127.0.0.1")
        assert remaining == 100

    def test_rate_limiter_reset(self):
        """Test rate limiter reset."""
        from src.middleware.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=100)
        limiter.requests["127.0.0.1"] = [datetime.now()]
        limiter.reset()
        assert len(limiter.requests) == 0
