"""Email notification service."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.models import ChangeEvent
from src.notifier.config import EmailConfig
from src.utils.logger import get_logger


class EmailNotifier:
    """Handles email notifications for outage changes."""

    def __init__(self, config: Optional[EmailConfig] = None):
        """
        Initialize email notifier.

        Args:
            config: Email configuration object
        """
        self.config = config or EmailConfig()
        self.logger = get_logger("email_notifier")

        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent.parent.parent / "templates"
        if template_dir.exists():
            self.template_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=True
            )
        else:
            self.template_env = None
            self.logger.warning(f"Template directory not found: {template_dir}")

    async def send_change_notification(
        self,
        changes: List[ChangeEvent],
        article_content: Optional[str] = None
    ) -> bool:
        """
        Send email notification for detected changes.

        Args:
            changes: List of change events
            article_content: Optional AI-generated article (Version 2)

        Returns:
            True if email was sent successfully
        """
        if not changes:
            self.logger.debug("No changes to notify")
            return True

        if not self.config.recipients_list:
            self.logger.warning("No email recipients configured")
            return False

        # Group changes by service
        changes_by_service = {}
        for change in changes:
            service = change.service_name
            if service not in changes_by_service:
                changes_by_service[service] = []
            changes_by_service[service].append(change)

        # Send email for each service with changes
        success = True
        for service_name, service_changes in changes_by_service.items():
            try:
                await self._send_service_notification(
                    service_name,
                    service_changes,
                    article_content
                )
            except Exception as e:
                self.logger.error(f"Failed to send notification for {service_name}: {e}")
                success = False

        return success

    async def _send_service_notification(
        self,
        service_name: str,
        changes: List[ChangeEvent],
        article_content: Optional[str] = None
    ) -> None:
        """Send notification for a specific service."""
        primary_change = changes[0]

        # Generate subject line
        subject = self._generate_subject(service_name, primary_change)

        # Generate HTML content
        if self.template_env and article_content:
            try:
                template = self.template_env.get_template("email_ai_article.html")
                html_content = template.render(
                    service_name=service_name,
                    article=article_content,
                    changes=changes,
                    timestamp=primary_change.timestamp,
                )
            except Exception:
                html_content = self._generate_basic_html(service_name, changes, article_content)
        elif self.template_env:
            try:
                template = self.template_env.get_template("email_basic.html")
                html_content = template.render(
                    service_name=service_name,
                    changes=changes,
                    primary_change=primary_change,
                    timestamp=primary_change.timestamp,
                )
            except Exception:
                html_content = self._generate_basic_html(service_name, changes)
        else:
            html_content = self._generate_basic_html(service_name, changes, article_content)

        # Send email
        await self._send_email(subject, html_content)
        self.logger.info(f"Email sent for {service_name} to {len(self.config.recipients_list)} recipients")

    async def _send_email(self, subject: str, html_content: str) -> None:
        """Send actual email via SMTP."""
        message = MIMEMultipart("alternative")
        message["From"] = self.config.sender_email
        message["To"] = ", ".join(self.config.recipients_list)
        message["Subject"] = subject

        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        try:
            with smtplib.SMTP(
                self.config.smtp_host,
                self.config.smtp_port,
                timeout=30
            ) as server:
                if self.config.use_tls:
                    server.starttls()

                if self.config.smtp_username and self.config.smtp_password:
                    server.login(
                        self.config.smtp_username,
                        self.config.smtp_password
                    )

                server.send_message(message)
                self.logger.debug("Email sent successfully via SMTP")

        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            raise

    def _generate_subject(self, service_name: str, change: ChangeEvent) -> str:
        """Generate email subject line."""
        change_type_messages = {
            "new_outage": f"[ALERT] {service_name} is experiencing issues",
            "status_changed": f"[UPDATE] {service_name} status changed",
            "severity_increased": f"[CRITICAL] {service_name} outage severity increased",
            "severity_decreased": f"[INFO] {service_name} outage severity decreased",
            "report_count_spike": f"[WARNING] {service_name} reports spiking",
            "outage_resolved": f"[RESOLVED] {service_name} issues resolved",
        }

        return change_type_messages.get(
            change.change_type.value,
            f"[UPDATE] {service_name} Status Update"
        )

    def _generate_basic_html(
        self,
        service_name: str,
        changes: List[ChangeEvent],
        article_content: Optional[str] = None
    ) -> str:
        """Generate basic HTML email when templates are not available."""
        changes_html = ""
        for change in changes:
            changes_html += f"""
            <div style="margin: 15px 0; padding: 10px; border-left: 3px solid #f44336; background-color: #f9f9f9;">
                <strong>{change.change_type.value.replace('_', ' ').title()}</strong>
                <p>Status: {change.new_status.value}</p>
                <p>Report Count: {change.new_report_count:,}</p>
                <p>Severity: {change.new_severity.value}</p>
                <p>Time: {change.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
            """

        article_section = ""
        if article_content:
            article_section = f"""
            <div style="margin: 20px 0; padding: 15px; background-color: #f0f0f0; border-radius: 5px;">
                <h3>AI Summary</h3>
                <p>{article_content}</p>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #f44336; color: white; padding: 20px; text-align: center;">
                <h1>Service Outage Alert</h1>
                <p>{service_name}</p>
            </div>

            <div style="padding: 20px;">
                <h2>Detected Changes</h2>
                {changes_html}
                {article_section}
                <p>
                    <a href="{changes[0].service_url}">View on DownDetector</a>
                </p>
            </div>

            <div style="padding: 20px; text-align: center; font-size: 0.9em; color: #666;">
                <p>Powered by DownDetector Outage Monitor</p>
                <p>This is an automated notification</p>
            </div>
        </body>
        </html>
        """
