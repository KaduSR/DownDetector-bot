"""Pydantic models for the outage monitoring system."""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StatusEnum(str, Enum):
    """Service status enumeration."""
    UP = "up"
    ISSUES = "issues"
    DOWN = "down"


class SeverityEnum(str, Enum):
    """Severity level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChangeType(str, Enum):
    """Types of changes that can be detected."""
    NEW_OUTAGE = "new_outage"
    STATUS_CHANGED = "status_changed"
    SEVERITY_INCREASED = "severity_increased"
    SEVERITY_DECREASED = "severity_decreased"
    REPORT_COUNT_SPIKE = "report_count_spike"
    OUTAGE_RESOLVED = "outage_resolved"


class OutageReport(BaseModel):
    """Outage report data model."""
    service_name: str = Field(..., description="Name of the service")
    service_url: str = Field(..., description="URL to DownDetector page")
    status: StatusEnum = Field(..., description="Current status")
    report_count: int = Field(..., ge=0, description="Number of user reports")
    timestamp: datetime = Field(..., description="Timestamp of the report")
    severity: SeverityEnum = Field(..., description="Severity level")
    affected_regions: List[str] = Field(
        default_factory=list,
        description="List of affected regions"
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the outage"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "Google",
                "service_url": "https://downdetector.com/status/google",
                "status": "down",
                "report_count": 15234,
                "timestamp": "2025-11-18T10:25:00Z",
                "severity": "critical",
                "affected_regions": ["US", "EU"],
                "description": "Search and Gmail issues"
            }
        }


class ChangeEvent(BaseModel):
    """Change event data model."""
    change_type: ChangeType = Field(..., description="Type of change detected")
    service_name: str = Field(..., description="Name of the service")
    old_status: Optional[StatusEnum] = Field(
        None,
        description="Previous status"
    )
    new_status: StatusEnum = Field(..., description="Current status")
    old_report_count: int = Field(
        0,
        ge=0,
        description="Previous report count"
    )
    new_report_count: int = Field(
        ...,
        ge=0,
        description="Current report count"
    )
    old_severity: Optional[SeverityEnum] = Field(
        None,
        description="Previous severity"
    )
    new_severity: SeverityEnum = Field(..., description="Current severity")
    timestamp: datetime = Field(..., description="Timestamp of the change")
    service_url: str = Field(..., description="URL to DownDetector page")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "change_type": self.change_type.value,
            "service_name": self.service_name,
            "old_status": self.old_status.value if self.old_status else None,
            "new_status": self.new_status.value,
            "old_report_count": self.old_report_count,
            "new_report_count": self.new_report_count,
            "old_severity": self.old_severity.value if self.old_severity else None,
            "new_severity": self.new_severity.value,
            "timestamp": self.timestamp.isoformat(),
            "service_url": self.service_url,
        }


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    uptime_seconds: int = Field(..., ge=0, description="Uptime in seconds")


class StatusResponse(BaseModel):
    """Status response model."""
    services: List[OutageReport]
    total_count: int = Field(..., ge=0)
    timestamp: datetime


class ChangesResponse(BaseModel):
    """Changes response model."""
    changes: List[ChangeEvent]
    total_count: int = Field(..., ge=0)
    time_range: Dict[str, str]


class MetricsResponse(BaseModel):
    """Metrics response model."""
    total_scrapes: int = Field(..., ge=0)
    successful_scrapes: int = Field(..., ge=0)
    failed_scrapes: int = Field(..., ge=0)
    total_notifications_sent: int = Field(..., ge=0)
    services_monitored: int = Field(..., ge=0)
    current_outages: int = Field(..., ge=0)
    uptime_seconds: int = Field(..., ge=0)
    success_rate: float = Field(..., ge=0)
    last_scrape: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: Dict[str, str]
    timestamp: datetime
