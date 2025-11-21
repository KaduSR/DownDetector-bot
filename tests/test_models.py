"""Tests for data models."""

import pytest
from datetime import datetime
from src.models import (
    OutageReport,
    ChangeEvent,
    StatusEnum,
    SeverityEnum,
    ChangeType,
)


class TestOutageReport:
    """Tests for OutageReport model."""

    def test_create_outage_report(self, sample_report):
        """Test creating an outage report."""
        assert sample_report.service_name == "Google"
        assert sample_report.status == StatusEnum.UP
        assert sample_report.report_count == 100
        assert sample_report.severity == SeverityEnum.LOW

    def test_outage_report_with_regions(self, sample_down_report):
        """Test outage report with affected regions."""
        assert len(sample_down_report.affected_regions) == 2
        assert "US" in sample_down_report.affected_regions

    def test_outage_report_serialization(self, sample_report):
        """Test outage report JSON serialization."""
        data = sample_report.model_dump()
        assert data["service_name"] == "Google"
        assert data["status"] == StatusEnum.UP


class TestChangeEvent:
    """Tests for ChangeEvent model."""

    def test_create_change_event(self):
        """Test creating a change event."""
        event = ChangeEvent(
            change_type=ChangeType.NEW_OUTAGE,
            service_name="Google",
            old_status=None,
            new_status=StatusEnum.DOWN,
            old_report_count=0,
            new_report_count=15000,
            old_severity=None,
            new_severity=SeverityEnum.CRITICAL,
            timestamp=datetime.now(),
            service_url="https://downdetector.com/status/google",
        )

        assert event.change_type == ChangeType.NEW_OUTAGE
        assert event.service_name == "Google"
        assert event.new_status == StatusEnum.DOWN

    def test_change_event_to_dict(self):
        """Test change event dictionary conversion."""
        event = ChangeEvent(
            change_type=ChangeType.STATUS_CHANGED,
            service_name="Facebook",
            old_status=StatusEnum.UP,
            new_status=StatusEnum.DOWN,
            old_report_count=100,
            new_report_count=5000,
            old_severity=SeverityEnum.LOW,
            new_severity=SeverityEnum.HIGH,
            timestamp=datetime.now(),
            service_url="https://downdetector.com/status/facebook",
        )

        data = event.to_dict()
        assert data["change_type"] == "status_changed"
        assert data["service_name"] == "Facebook"
        assert data["old_status"] == "up"
        assert data["new_status"] == "down"


class TestEnums:
    """Tests for enum types."""

    def test_status_enum(self):
        """Test status enumeration."""
        assert StatusEnum.UP.value == "up"
        assert StatusEnum.ISSUES.value == "issues"
        assert StatusEnum.DOWN.value == "down"

    def test_severity_enum(self):
        """Test severity enumeration."""
        assert SeverityEnum.LOW.value == "low"
        assert SeverityEnum.MEDIUM.value == "medium"
        assert SeverityEnum.HIGH.value == "high"
        assert SeverityEnum.CRITICAL.value == "critical"

    def test_change_type_enum(self):
        """Test change type enumeration."""
        assert ChangeType.NEW_OUTAGE.value == "new_outage"
        assert ChangeType.OUTAGE_RESOLVED.value == "outage_resolved"
