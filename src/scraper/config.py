"""Configuration for the scraper service."""

from pydantic_settings import BaseSettings
from typing import List


class ScraperConfig(BaseSettings):
    """Configuration for scraper service."""

    scrape_interval_minutes: int = 10
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    user_agent: str = "Mozilla/5.0 (compatible; OutageBot/1.0)"
    monitored_services: str = "google,facebook,twitter,instagram,whatsapp"

    @property
    def services_list(self) -> List[str]:
        """Get list of monitored services."""
        return [s.strip().lower() for s in self.monitored_services.split(",")]

    class Config:
        env_prefix = "SCRAPER_"
