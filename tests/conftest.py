"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime
from src.models import OutageReport, StatusEnum, SeverityEnum


@pytest.fixture
def sample_report():
    """Create a sample outage report for testing."""
    return OutageReport(
        service_name="Google",
        service_url="https://downdetector.com/status/google",
        status=StatusEnum.UP,
        report_count=100,
        timestamp=datetime.now(),
        severity=SeverityEnum.LOW,
        affected_regions=[],
    )


@pytest.fixture
def sample_down_report():
    """Create a sample outage report with down status."""
    return OutageReport(
        service_name="Google",
        service_url="https://downdetector.com/status/google",
        status=StatusEnum.DOWN,
        report_count=15000,
        timestamp=datetime.now(),
        severity=SeverityEnum.CRITICAL,
        affected_regions=["US", "EU"],
        description="Major outage affecting search and Gmail",
    )


@pytest.fixture
def multiple_reports():
    """Create multiple sample reports for testing."""
    return [
        OutageReport(
            service_name="Google",
            service_url="https://downdetector.com/status/google",
            status=StatusEnum.DOWN,
            report_count=15000,
            timestamp=datetime.now(),
            severity=SeverityEnum.CRITICAL,
            affected_regions=["US"],
        ),
        OutageReport(
            service_name="Facebook",
            service_url="https://downdetector.com/status/facebook",
            status=StatusEnum.ISSUES,
            report_count=5000,
            timestamp=datetime.now(),
            severity=SeverityEnum.HIGH,
            affected_regions=["EU"],
        ),
        OutageReport(
            service_name="Twitter",
            service_url="https://downdetector.com/status/twitter",
            status=StatusEnum.UP,
            report_count=50,
            timestamp=datetime.now(),
            severity=SeverityEnum.LOW,
            affected_regions=[],
        ),
    ]
