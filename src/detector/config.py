"""Configuration for the change detector."""

from pydantic_settings import BaseSettings


class DetectorConfig(BaseSettings):
    """Configuration for change detector."""

    report_count_threshold: int = 1000

    class Config:
        env_prefix = "DETECTOR_"
