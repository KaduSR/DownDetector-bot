"""System metrics collection for the outage monitoring system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class SystemMetrics:
    """System metrics data class for tracking application statistics."""

    total_scrapes: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    total_notifications_sent: int = 0
    services_monitored: int = 0
    current_outages: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_scrape: Optional[datetime] = None

    def increment_scrapes(self, success: bool = True) -> None:
        """Increment scrape counter."""
        self.total_scrapes += 1
        if success:
            self.successful_scrapes += 1
        else:
            self.failed_scrapes += 1
        self.last_scrape = datetime.now()

    def increment_notifications(self, count: int = 1) -> None:
        """Increment notification counter."""
        self.total_notifications_sent += count

    def update_services_count(self, count: int) -> None:
        """Update monitored services count."""
        self.services_monitored = count

    def update_outages_count(self, count: int) -> None:
        """Update current outages count."""
        self.current_outages = count

    def get_uptime_seconds(self) -> int:
        """Calculate uptime in seconds."""
        return int((datetime.now() - self.start_time).total_seconds())

    def get_success_rate(self) -> float:
        """Calculate scrape success rate."""
        if self.total_scrapes == 0:
            return 100.0
        return (self.successful_scrapes / self.total_scrapes) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        return {
            "total_scrapes": self.total_scrapes,
            "successful_scrapes": self.successful_scrapes,
            "failed_scrapes": self.failed_scrapes,
            "total_notifications_sent": self.total_notifications_sent,
            "services_monitored": self.services_monitored,
            "current_outages": self.current_outages,
            "uptime_seconds": self.get_uptime_seconds(),
            "success_rate": round(self.get_success_rate(), 2),
            "last_scrape": self.last_scrape.isoformat() if self.last_scrape else None,
        }

    def reset(self) -> None:
        """Reset all metrics to initial values."""
        self.total_scrapes = 0
        self.successful_scrapes = 0
        self.failed_scrapes = 0
        self.total_notifications_sent = 0
        self.services_monitored = 0
        self.current_outages = 0
        self.start_time = datetime.now()
        self.last_scrape = None


# Global metrics instance
metrics = SystemMetrics()
