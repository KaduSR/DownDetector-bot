"""Configuration for notification services."""

from pydantic_settings import BaseSettings
from typing import List


class EmailConfig(BaseSettings):
    """Email configuration."""

    smtp_host: str = "localhost"
    smtp_port: int = 587
    use_tls: bool = True
    smtp_username: str = ""
    smtp_password: str = ""
    sender_email: str = "notifications@localhost"
    recipient_emails: str = ""

    @property
    def recipients_list(self) -> List[str]:
        """Get list of recipient emails."""
        if not self.recipient_emails:
            return []
        return [e.strip() for e in self.recipient_emails.split(",") if e.strip()]

    class Config:
        env_prefix = "EMAIL_"
