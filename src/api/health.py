"""Health check endpoints."""

from datetime import datetime
from fastapi import APIRouter

from src.models import HealthCheckResponse, MetricsResponse
from src.utils.metrics import metrics
from src import __version__

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns system health status and uptime information.
    """
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=__version__,
        uptime_seconds=metrics.get_uptime_seconds(),
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    Get system metrics.

    Returns detailed system metrics including scrape statistics,
    notification counts, and uptime information.
    """
    return MetricsResponse(
        total_scrapes=metrics.total_scrapes,
        successful_scrapes=metrics.successful_scrapes,
        failed_scrapes=metrics.failed_scrapes,
        total_notifications_sent=metrics.total_notifications_sent,
        services_monitored=metrics.services_monitored,
        current_outages=metrics.current_outages,
        uptime_seconds=metrics.get_uptime_seconds(),
        success_rate=round(metrics.get_success_rate(), 2),
        last_scrape=metrics.last_scrape,
    )
