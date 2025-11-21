"""Scheduler for periodic outage monitoring."""

import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.scraper import DownDetectorScraper, ScraperConfig
from src.detector import ChangeDetector, DetectorConfig
from src.notifier import EmailNotifier, WebSocketNotifier, EmailConfig
from src.ai import AIArticleGenerator, AIConfig
from src.utils.logger import get_logger
from src.utils.metrics import metrics


class OutageMonitorScheduler:
    """Orchestrates the scraping and notification process."""

    def __init__(
        self,
        scraper_config: Optional[ScraperConfig] = None,
        detector_config: Optional[DetectorConfig] = None,
        email_config: Optional[EmailConfig] = None,
        ai_config: Optional[AIConfig] = None,
        enable_ai: bool = False,
    ):
        """
        Initialize scheduler with all components.

        Args:
            scraper_config: Scraper configuration
            detector_config: Change detector configuration
            email_config: Email notification configuration
            ai_config: AI article generator configuration
            enable_ai: Whether to enable AI article generation
        """
        self.logger = get_logger("scheduler")

        # Initialize components
        self.scraper = DownDetectorScraper(scraper_config or ScraperConfig())
        self.detector = ChangeDetector(detector_config or DetectorConfig())
        self.email_notifier = EmailNotifier(email_config or EmailConfig())
        self.ws_notifier = WebSocketNotifier()

        # AI generator (optional)
        self.ai_generator: Optional[AIArticleGenerator] = None
        if enable_ai:
            self.ai_generator = AIArticleGenerator(ai_config or AIConfig())

        # Scheduler
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.interval_minutes = (scraper_config or ScraperConfig()).scrape_interval_minutes

    def start(self) -> None:
        """Start the scheduler."""
        if self.is_running:
            self.logger.warning("Scheduler already running")
            return

        # Add monitoring job
        self.scheduler.add_job(
            func=self._run_monitoring_cycle,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="outage_monitor",
            name="Outage Monitoring Job",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True
        self.logger.info(f"Scheduler started. Monitoring every {self.interval_minutes} minutes.")

        # Run immediately on start
        asyncio.create_task(self._run_monitoring_cycle())

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.is_running:
            return

        self.scheduler.shutdown(wait=False)
        self.is_running = False
        self.logger.info("Scheduler stopped.")

    async def _run_monitoring_cycle(self) -> None:
        """Run a single monitoring cycle."""
        self.logger.info(f"[{datetime.now()}] Starting monitoring cycle...")

        try:
            # Step 1: Scrape DownDetector
            reports = await self.scraper.scrape_all_services()
            metrics.increment_scrapes(success=len(reports) > 0)
            metrics.update_services_count(len(reports))

            self.logger.info(f"Scraped {len(reports)} services")

            if not reports:
                self.logger.warning("No reports found, skipping cycle")
                return

            # Count current outages
            outages = sum(1 for r in reports if r.status.value != "up")
            metrics.update_outages_count(outages)

            # Step 2: Detect changes
            changes = self.detector.detect_changes(reports)
            self.logger.info(f"Detected {len(changes)} changes")

            if not changes:
                self.logger.debug("No changes detected, skipping notifications")
                return

            # Step 3: Generate AI article (if enabled)
            article = None
            if self.ai_generator:
                article = await self.ai_generator.generate_article(changes)
                if article:
                    self.logger.info("AI article generated successfully")

            # Step 4: Send notifications
            # Email notifications
            await self.email_notifier.send_change_notification(changes, article)
            metrics.increment_notifications(len(changes))
            self.logger.info("Email notifications sent")

            # WebSocket notifications
            await self.ws_notifier.broadcast_changes(changes)
            self.logger.info("WebSocket notifications sent")

            self.logger.info(f"[{datetime.now()}] Monitoring cycle completed successfully")

        except Exception as e:
            self.logger.error(f"Error during monitoring cycle: {e}")
            metrics.increment_scrapes(success=False)

    async def run_manual_cycle(self) -> dict:
        """
        Run a manual monitoring cycle and return results.

        Returns:
            Dictionary with cycle results
        """
        self.logger.info("Running manual monitoring cycle")

        try:
            reports = await self.scraper.scrape_all_services()
            changes = self.detector.detect_changes(reports)

            return {
                "success": True,
                "reports_count": len(reports),
                "changes_count": len(changes),
                "changes": [c.to_dict() for c in changes],
            }
        except Exception as e:
            self.logger.error(f"Manual cycle failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_websocket_app(self):
        """Get WebSocket ASGI app."""
        return self.ws_notifier.get_asgi_app()

    def get_current_state(self):
        """Get current detector state."""
        return self.detector.get_current_state()
