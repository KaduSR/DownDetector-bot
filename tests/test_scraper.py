"""Tests for scraper service."""

import pytest
from src.scraper import DownDetectorScraper, ScraperConfig
from src.models import SeverityEnum


class TestScraperConfig:
    """Tests for scraper configuration."""

    def test_default_config(self):
        """Test default scraper configuration."""
        config = ScraperConfig()
        assert config.scrape_interval_minutes == 10
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3

    def test_services_list(self):
        """Test services list parsing."""
        config = ScraperConfig(monitored_services="google,facebook,twitter")
        services = config.services_list
        assert len(services) == 3
        assert "google" in services
        assert "facebook" in services

    def test_services_list_with_spaces(self):
        """Test services list parsing with spaces."""
        config = ScraperConfig(monitored_services="google, facebook , twitter")
        services = config.services_list
        assert services == ["google", "facebook", "twitter"]


class TestDownDetectorScraper:
    """Tests for DownDetectorScraper class."""

    def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = DownDetectorScraper()
        assert scraper.BASE_URL == "https://downdetector.com"
        assert scraper.client is None

    def test_severity_calculation(self):
        """Test severity calculation based on report count."""
        scraper = DownDetectorScraper()

        assert scraper._calculate_severity(500) == SeverityEnum.LOW
        assert scraper._calculate_severity(1500) == SeverityEnum.MEDIUM
        assert scraper._calculate_severity(6000) == SeverityEnum.HIGH
        assert scraper._calculate_severity(15000) == SeverityEnum.CRITICAL

    def test_severity_boundaries(self):
        """Test severity calculation at boundaries."""
        scraper = DownDetectorScraper()

        assert scraper._calculate_severity(999) == SeverityEnum.LOW
        assert scraper._calculate_severity(1000) == SeverityEnum.LOW
        assert scraper._calculate_severity(1001) == SeverityEnum.MEDIUM
        assert scraper._calculate_severity(5000) == SeverityEnum.MEDIUM
        assert scraper._calculate_severity(5001) == SeverityEnum.HIGH
        assert scraper._calculate_severity(10000) == SeverityEnum.HIGH
        assert scraper._calculate_severity(10001) == SeverityEnum.CRITICAL


class TestStatusParsing:
    """Tests for status parsing logic."""

    def test_parse_status_down(self):
        """Test parsing down status."""
        scraper = DownDetectorScraper()

        assert scraper._parse_status("Major outage").value == "down"
        assert scraper._parse_status("Service down").value == "down"
        assert scraper._parse_status("problem detected").value == "down"

    def test_parse_status_issues(self):
        """Test parsing issues status."""
        scraper = DownDetectorScraper()

        assert scraper._parse_status("Possible problems").value == "issues"
        assert scraper._parse_status("Warning detected").value == "issues"

    def test_parse_status_up(self):
        """Test parsing up status."""
        scraper = DownDetectorScraper()

        assert scraper._parse_status("No problems").value == "up"
        assert scraper._parse_status("All systems operational").value == "up"

    def _parse_status(self, text: str):
        """Helper to test status parsing."""
        from src.models import StatusEnum
        text_lower = text.lower()
        if "down" in text_lower or "major" in text_lower or "problem" in text_lower:
            return StatusEnum.DOWN
        elif "possible" in text_lower or "warning" in text_lower:
            return StatusEnum.ISSUES
        return StatusEnum.UP
