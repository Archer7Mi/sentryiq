"""Configuration for data ingestion workers.

Environment-based settings using Pydantic for validation.
"""

import os
from datetime import datetime, timedelta

from pydantic import BaseSettings, Field


class IngestionConfig(BaseSettings):
    """Ingestion worker configuration."""

    # NVD API Configuration
    nvd_api_url: str = Field(
        default="https://services.nvd.nist.gov/rest/json/cves/2.0",
        description="NVD API v2.0 base URL",
    )
    nvd_api_key: str = Field(
        default="",
        description="Optional NVD API key (increases rate limits)",
    )
    nvd_page_size: int = Field(
        default=2000, ge=1, le=2000, description="CVE records per API page"
    )
    nvd_results_per_request: int = Field(
        default=2000, ge=1, le=2000, description="Results per request"
    )
    nvd_start_index: int = Field(
        default=0, ge=0, description="Pagination start index"
    )
    nvd_poll_interval_hours: int = Field(
        default=2, description="NVD polling interval in hours"
    )

    # CISA KEV Configuration
    kev_url: str = Field(
        default="https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        description="CISA Known Exploited Vulnerabilities JSON URL",
    )
    kev_sync_interval_hours: int = Field(
        default=6, description="KEV sync interval in hours"
    )

    # FIRST EPSS Configuration
    epss_api_url: str = Field(
        default="https://api.first.org/data/v1/epss",
        description="FIRST EPSS API base URL",
    )
    epss_page_size: int = Field(
        default=25000, ge=1, le=25000, description="EPSS records per page"
    )
    epss_poll_interval_hours: int = Field(
        default=24, description="EPSS polling interval in hours (daily)"
    )

    # Retry Configuration
    max_retries: int = Field(default=3, description="Max API request retries")
    retry_backoff_factor: float = Field(
        default=1.5, description="Exponential backoff multiplier"
    )
    timeout_seconds: int = Field(
        default=30, description="HTTP request timeout in seconds"
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/sentryiq",
        description="PostgreSQL async connection string",
    )

    class Config:
        """Pydantic config."""
        env_prefix = "SENTRYIQ_"
        case_sensitive = False


# Singleton instance
config = IngestionConfig()
