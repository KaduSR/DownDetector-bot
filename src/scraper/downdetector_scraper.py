"""DownDetector web scraper for outage information."""

from typing import List, Optional
from datetime import datetime
import asyncio
import httpx
from bs4 import BeautifulSoup

from src.models import OutageReport, StatusEnum, SeverityEnum
from src.scraper.config import ScraperConfig
from src.utils.logger import get_logger


class DownDetectorScraper:
    """Scraper for DownDetector.com outage information."""

    BASE_URL = "https://downdetector.com"

    def __init__(self, config: Optional[ScraperConfig] = None):
        """
        Initialize DownDetector scraper.

        Args:
            config: Optional scraper configuration
        """
        self.config = config or ScraperConfig()
        self.logger = get_logger("scraper")
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.config.timeout_seconds,
                headers={
                    "User-Agent": self.config.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                follow_redirects=True,
            )
        return self.client

    async def scrape_all_services(self) -> List[OutageReport]:
        """
        Scrape all configured services from DownDetector.

        Returns:
            List of OutageReport objects
        """
        reports = []
        services = self.config.services_list

        self.logger.info(f"Starting scrape for {len(services)} services")

        for service in services:
            for attempt in range(self.config.retry_attempts):
                try:
                    report = await self.scrape_service(service)
                    if report:
                        reports.append(report)
                        self.logger.debug(f"Successfully scraped {service}")
                    break
                except Exception as e:
                    if attempt < self.config.retry_attempts - 1:
                        self.logger.warning(
                            f"Attempt {attempt + 1} failed for {service}: {e}. Retrying..."
                        )
                        await asyncio.sleep(self.config.retry_delay_seconds)
                    else:
                        self.logger.error(
                            f"Failed to scrape {service} after {self.config.retry_attempts} attempts: {e}"
                        )

        self.logger.info(f"Scraping complete. Retrieved {len(reports)} reports")
        return reports

    async def scrape_service(self, service_name: str) -> Optional[OutageReport]:
        """
        Scrape outage information for a specific service.

        Args:
            service_name: Name of the service to scrape

        Returns:
            OutageReport or None if scraping fails
        """
        client = await self._get_client()
        service_url = f"{self.BASE_URL}/status/{service_name}"

        try:
            response = await client.get(service_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            return self._parse_service_page(soup, service_name, service_url)

        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error for {service_name}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            self.logger.error(f"Request error for {service_name}: {e}")
            return None

    def _parse_service_page(
        self,
        soup: BeautifulSoup,
        service_name: str,
        service_url: str
    ) -> Optional[OutageReport]:
        """
        Parse the service page HTML to extract outage information.

        Args:
            soup: BeautifulSoup object of the page
            service_name: Name of the service
            service_url: URL of the service page

        Returns:
            OutageReport or None
        """
        try:
            # Extract status indicator
            status = self._extract_status(soup)

            # Extract report count
            report_count = self._extract_report_count(soup)

            # Extract affected regions (if available)
            affected_regions = self._extract_regions(soup)

            # Extract description
            description = self._extract_description(soup)

            # Calculate severity based on report count
            severity = self._calculate_severity(report_count)

            return OutageReport(
                service_name=service_name.title(),
                service_url=service_url,
                status=status,
                report_count=report_count,
                timestamp=datetime.now(),
                severity=severity,
                affected_regions=affected_regions,
                description=description,
            )

        except Exception as e:
            self.logger.error(f"Error parsing page for {service_name}: {e}")
            return None

    def _extract_status(self, soup: BeautifulSoup) -> StatusEnum:
        """Extract service status from page."""
        # Try to find status indicator elements
        # These selectors are based on typical DownDetector page structure
        status_selectors = [
            ".entry-title",
            ".status-title",
            "h1",
            ".company-status",
        ]

        for selector in status_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().lower()
                if "problem" in text or "issue" in text or "outage" in text:
                    return StatusEnum.DOWN
                elif "possible" in text or "warning" in text:
                    return StatusEnum.ISSUES

        # Check for report chart or baseline
        chart = soup.select_one(".chart-container")
        if chart:
            # If there's significant chart activity, there might be issues
            return StatusEnum.ISSUES

        return StatusEnum.UP

    def _extract_report_count(self, soup: BeautifulSoup) -> int:
        """Extract number of user reports."""
        # Try various selectors for report count
        count_selectors = [
            ".reports-count",
            ".report-count",
            ".count",
            "[data-reports]",
        ]

        for selector in count_selectors:
            element = soup.select_one(selector)
            if element:
                try:
                    text = element.get_text().strip()
                    # Extract numbers from text
                    numbers = "".join(c for c in text if c.isdigit())
                    if numbers:
                        return int(numbers)
                except ValueError:
                    continue

        # Try to find any element with numbers that might be report count
        # Look for patterns like "X reports"
        import re
        text = soup.get_text()
        match = re.search(r"(\d+(?:,\d+)*)\s*(?:report|user)", text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))

        return 0

    def _extract_regions(self, soup: BeautifulSoup) -> List[str]:
        """Extract affected regions from page."""
        regions = []

        # Look for region/location elements
        region_selectors = [
            ".affected-region",
            ".region",
            ".location-item",
            ".city-item",
        ]

        for selector in region_selectors:
            elements = soup.select(selector)
            for element in elements:
                region = element.get_text().strip()
                if region and region not in regions:
                    regions.append(region)

        return regions[:10]  # Limit to 10 regions

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description or summary of the outage."""
        desc_selectors = [
            ".entry-content p",
            ".description",
            ".summary",
            "meta[name='description']",
        ]

        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    return element.get("content", "")[:500]
                text = element.get_text().strip()
                if text and len(text) > 20:
                    return text[:500]

        return None

    def _calculate_severity(self, report_count: int) -> SeverityEnum:
        """
        Calculate severity level based on report count.

        Args:
            report_count: Number of user reports

        Returns:
            Severity level
        """
        if report_count > 10000:
            return SeverityEnum.CRITICAL
        elif report_count > 5000:
            return SeverityEnum.HIGH
        elif report_count > 1000:
            return SeverityEnum.MEDIUM
        return SeverityEnum.LOW

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.logger.debug("HTTP client closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
