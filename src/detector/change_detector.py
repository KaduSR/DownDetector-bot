"""Change detection system for identifying outage status changes."""

from typing import List, Dict, Optional
from datetime import datetime

from src.models import OutageReport, ChangeEvent, ChangeType, StatusEnum, SeverityEnum
from src.detector.config import DetectorConfig
from src.utils.logger import get_logger


class ChangeDetector:
    """Detects changes between scraping cycles."""

    SEVERITY_ORDER = [SeverityEnum.LOW, SeverityEnum.MEDIUM, SeverityEnum.HIGH, SeverityEnum.CRITICAL]

    def __init__(self, config: Optional[DetectorConfig] = None):
        """
        Initialize change detector.

        Args:
            config: Optional detector configuration
        """
        self.config = config or DetectorConfig()
        self.previous_state: Dict[str, OutageReport] = {}
        self.logger = get_logger("detector")

    def detect_changes(self, current_reports: List[OutageReport]) -> List[ChangeEvent]:
        """
        Detect changes between previous and current states.

        Args:
            current_reports: List of current outage reports

        Returns:
            List of detected change events
        """
        changes = []
        current_services = {report.service_name: report for report in current_reports}

        self.logger.debug(f"Comparing {len(current_reports)} current reports with {len(self.previous_state)} previous")

        # Check for new outages and changes in existing services
        for service_name, report in current_services.items():
            if service_name not in self.previous_state:
                # New service detected
                if report.status != StatusEnum.UP:
                    changes.append(self._create_change_event(
                        ChangeType.NEW_OUTAGE,
                        service_name,
                        None,
                        report
                    ))
                    self.logger.info(f"New outage detected: {service_name}")
            else:
                # Check for changes in existing service
                old_report = self.previous_state[service_name]
                detected_changes = self._compare_reports(old_report, report)
                changes.extend(detected_changes)

        # Check for resolved outages (services that were in previous state but not in current)
        for service_name, old_report in self.previous_state.items():
            if service_name not in current_services:
                if old_report.status != StatusEnum.UP:
                    # Create a resolved report
                    resolved_report = OutageReport(
                        service_name=old_report.service_name,
                        service_url=old_report.service_url,
                        status=StatusEnum.UP,
                        report_count=0,
                        timestamp=datetime.now(),
                        severity=SeverityEnum.LOW,
                        affected_regions=[],
                    )
                    changes.append(self._create_change_event(
                        ChangeType.OUTAGE_RESOLVED,
                        service_name,
                        old_report,
                        resolved_report
                    ))
                    self.logger.info(f"Outage resolved: {service_name}")

        # Update state
        self.previous_state = current_services.copy()

        self.logger.info(f"Detected {len(changes)} changes")
        return changes

    def _compare_reports(
        self,
        old_report: OutageReport,
        new_report: OutageReport
    ) -> List[ChangeEvent]:
        """
        Compare two reports and detect changes.

        Args:
            old_report: Previous report
            new_report: Current report

        Returns:
            List of detected changes
        """
        changes = []
        service_name = new_report.service_name

        # Status change
        if old_report.status != new_report.status:
            if new_report.status == StatusEnum.UP:
                change_type = ChangeType.OUTAGE_RESOLVED
                self.logger.info(f"Status change (resolved): {service_name}")
            else:
                change_type = ChangeType.STATUS_CHANGED
                self.logger.info(f"Status change: {service_name} {old_report.status} -> {new_report.status}")

            changes.append(self._create_change_event(
                change_type,
                service_name,
                old_report,
                new_report
            ))

        # Severity change (only if status hasn't changed to UP)
        if new_report.status != StatusEnum.UP:
            old_severity_idx = self.SEVERITY_ORDER.index(old_report.severity)
            new_severity_idx = self.SEVERITY_ORDER.index(new_report.severity)

            if new_severity_idx > old_severity_idx:
                changes.append(self._create_change_event(
                    ChangeType.SEVERITY_INCREASED,
                    service_name,
                    old_report,
                    new_report
                ))
                self.logger.info(f"Severity increased: {service_name}")
            elif new_severity_idx < old_severity_idx:
                changes.append(self._create_change_event(
                    ChangeType.SEVERITY_DECREASED,
                    service_name,
                    old_report,
                    new_report
                ))
                self.logger.info(f"Severity decreased: {service_name}")

        # Report count spike
        count_increase = new_report.report_count - old_report.report_count
        if count_increase >= self.config.report_count_threshold:
            changes.append(self._create_change_event(
                ChangeType.REPORT_COUNT_SPIKE,
                service_name,
                old_report,
                new_report
            ))
            self.logger.info(f"Report count spike: {service_name} (+{count_increase})")

        return changes

    def _create_change_event(
        self,
        change_type: ChangeType,
        service_name: str,
        old_report: Optional[OutageReport],
        new_report: OutageReport
    ) -> ChangeEvent:
        """Create a ChangeEvent object."""
        return ChangeEvent(
            change_type=change_type,
            service_name=service_name,
            old_status=old_report.status if old_report else None,
            new_status=new_report.status,
            old_report_count=old_report.report_count if old_report else 0,
            new_report_count=new_report.report_count,
            old_severity=old_report.severity if old_report else None,
            new_severity=new_report.severity,
            timestamp=datetime.now(),
            service_url=new_report.service_url,
        )

    def reset_state(self) -> None:
        """Reset the internal state."""
        self.previous_state = {}
        self.logger.info("Change detector state reset")

    def get_current_state(self) -> Dict[str, OutageReport]:
        """Get the current state (copy)."""
        return self.previous_state.copy()
