"""REST API routes for outage status and changes."""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, Request

from src.models import (
    OutageReport,
    StatusResponse,
    ChangesResponse,
    ErrorResponse,
    StatusEnum,
    SeverityEnum,
)
from src.middleware.rate_limiter import RateLimiter

router = APIRouter(prefix="/api/v1", tags=["Outage API"])

# Rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=100)

# In-memory storage for current state and changes history
_current_state: dict = {}
_changes_history: List[dict] = []


def set_current_state(state: dict) -> None:
    """Set current state from scheduler."""
    global _current_state
    _current_state = state


def add_changes(changes: List[dict]) -> None:
    """Add changes to history."""
    global _changes_history
    _changes_history.extend(changes)
    # Keep only last 24 hours of changes
    cutoff = datetime.now() - timedelta(hours=24)
    _changes_history = [
        c for c in _changes_history
        if datetime.fromisoformat(c.get("timestamp", "2000-01-01")) > cutoff
    ]


async def check_rate_limit(request: Request):
    """Dependency for rate limiting."""
    await rate_limiter.check_rate_limit(request)


@router.get(
    "/status",
    response_model=StatusResponse,
    responses={429: {"model": ErrorResponse}},
)
async def get_all_status(
    request: Request,
    severity: Optional[SeverityEnum] = Query(None, description="Filter by severity"),
    status: Optional[StatusEnum] = Query(None, description="Filter by status"),
    _: None = Depends(check_rate_limit),
) -> StatusResponse:
    """
    Get current status of all monitored services.

    Optionally filter by severity level or status.
    """
    services = list(_current_state.values())

    # Apply filters
    if severity:
        services = [s for s in services if s.severity == severity]
    if status:
        services = [s for s in services if s.status == status]

    return StatusResponse(
        services=services,
        total_count=len(services),
        timestamp=datetime.now(),
    )


@router.get(
    "/status/{service_name}",
    response_model=OutageReport,
    responses={404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def get_service_status(
    service_name: str,
    request: Request,
    _: None = Depends(check_rate_limit),
) -> OutageReport:
    """
    Get status for a specific service.

    Args:
        service_name: Name of the service (case-insensitive)
    """
    # Case-insensitive lookup
    service_name_lower = service_name.lower()
    for name, report in _current_state.items():
        if name.lower() == service_name_lower:
            return report

    raise HTTPException(
        status_code=404,
        detail={
            "error": {
                "code": "NOT_FOUND",
                "message": "Service not found",
                "details": f"The service '{service_name}' is not being monitored",
            },
            "timestamp": datetime.now().isoformat(),
        }
    )


@router.get(
    "/changes",
    response_model=ChangesResponse,
    responses={429: {"model": ErrorResponse}},
)
async def get_recent_changes(
    request: Request,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    change_type: Optional[str] = Query(None, description="Filter by change type"),
    _: None = Depends(check_rate_limit),
) -> ChangesResponse:
    """
    Get recent changes in the specified time range.

    Args:
        hours: Number of hours to look back (1-168, default 24)
        service: Optional service name filter
        change_type: Optional change type filter
    """
    cutoff = datetime.now() - timedelta(hours=hours)
    changes = []

    for change in _changes_history:
        change_time = datetime.fromisoformat(change.get("timestamp", "2000-01-01"))
        if change_time < cutoff:
            continue

        if service and change.get("service_name", "").lower() != service.lower():
            continue

        if change_type and change.get("change_type") != change_type:
            continue

        changes.append(change)

    return ChangesResponse(
        changes=changes,
        total_count=len(changes),
        time_range={
            "start": cutoff.isoformat(),
            "end": datetime.now().isoformat(),
        }
    )


@router.get("/services")
async def list_services(
    request: Request,
    _: None = Depends(check_rate_limit),
) -> dict:
    """
    List all monitored services.

    Returns a simple list of service names being monitored.
    """
    return {
        "services": list(_current_state.keys()),
        "count": len(_current_state),
        "timestamp": datetime.now().isoformat(),
    }
