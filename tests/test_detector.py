"""Tests for change detection system."""

import pytest
from datetime import datetime
from src.detector import ChangeDetector, DetectorConfig
from src.models import OutageReport, StatusEnum, SeverityEnum, ChangeType


class TestChangeDetector:
    """Tests for ChangeDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a change detector instance."""
        return ChangeDetector(DetectorConfig(report_count_threshold=1000))

    def test_new_outage_detection(self, detector, sample_down_report):
        """Test detection of new outage."""
        changes = detector.detect_changes([sample_down_report])

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.NEW_OUTAGE
        assert changes[0].service_name == "Google"

    def test_no_changes_when_status_unchanged(self, detector, sample_report):
        """Test no changes when status is unchanged."""
        # First scrape
        detector.detect_changes([sample_report])

        # Second scrape with same data
        changes = detector.detect_changes([sample_report])

        assert len(changes) == 0

    def test_status_change_detection(self, detector, sample_report):
        """Test detection of status change."""
        # First scrape - service up
        detector.detect_changes([sample_report])

        # Second scrape - service down
        sample_report.status = StatusEnum.DOWN
        sample_report.severity = SeverityEnum.HIGH
        changes = detector.detect_changes([sample_report])

        assert len(changes) >= 1
        status_changes = [c for c in changes if c.change_type == ChangeType.STATUS_CHANGED]
        assert len(status_changes) == 1

    def test_outage_resolved_detection(self, detector, sample_down_report):
        """Test detection of resolved outage."""
        # First scrape - service down
        detector.detect_changes([sample_down_report])

        # Second scrape - service up
        sample_down_report.status = StatusEnum.UP
        sample_down_report.severity = SeverityEnum.LOW
        sample_down_report.report_count = 0
        changes = detector.detect_changes([sample_down_report])

        resolved_changes = [c for c in changes if c.change_type == ChangeType.OUTAGE_RESOLVED]
        assert len(resolved_changes) == 1

    def test_severity_increase_detection(self, detector):
        """Test detection of severity increase."""
        # First scrape - low severity
        report = OutageReport(
            service_name="Test",
            service_url="https://example.com",
            status=StatusEnum.ISSUES,
            report_count=500,
            timestamp=datetime.now(),
            severity=SeverityEnum.LOW,
            affected_regions=[],
        )
        detector.detect_changes([report])

        # Second scrape - high severity
        report.severity = SeverityEnum.HIGH
        report.report_count = 6000
        changes = detector.detect_changes([report])

        severity_changes = [c for c in changes if c.change_type == ChangeType.SEVERITY_INCREASED]
        assert len(severity_changes) == 1

    def test_report_count_spike_detection(self, detector):
        """Test detection of report count spike."""
        # First scrape
        report = OutageReport(
            service_name="Test",
            service_url="https://example.com",
            status=StatusEnum.ISSUES,
            report_count=500,
            timestamp=datetime.now(),
            severity=SeverityEnum.MEDIUM,
            affected_regions=[],
        )
        detector.detect_changes([report])

        # Second scrape with spike (>1000 increase)
        report.report_count = 5000
        changes = detector.detect_changes([report])

        spike_changes = [c for c in changes if c.change_type == ChangeType.REPORT_COUNT_SPIKE]
        assert len(spike_changes) == 1

    def test_no_notification_for_up_service(self, detector, sample_report):
        """Test no notification for service that's always up."""
        # First scrape - service up
        changes = detector.detect_changes([sample_report])

        # Should not create NEW_OUTAGE for up service
        assert len(changes) == 0

    def test_reset_state(self, detector, sample_report):
        """Test state reset."""
        detector.detect_changes([sample_report])
        assert len(detector.previous_state) > 0

        detector.reset_state()
        assert len(detector.previous_state) == 0

    def test_multiple_services(self, detector, multiple_reports):
        """Test detection with multiple services."""
        changes = detector.detect_changes(multiple_reports)

        # Should detect outages for Google (down) and Facebook (issues)
        outage_changes = [c for c in changes if c.change_type == ChangeType.NEW_OUTAGE]
        assert len(outage_changes) == 2
