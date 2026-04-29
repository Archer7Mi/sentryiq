"""NVD API v2.0 polling worker.

Fetches new and modified CVE records from the National Vulnerability Database
on a scheduled interval (default: every 2 hours).
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from database.connection import get_engine, async_session_factory
from database.models import CVERecord
from ingestion.config import config

logger = logging.getLogger(__name__)


class NVDWorker:
    """NVD API v2.0 polling worker.
    
    Polls the National Vulnerability Database for new CVE records
    and updates existing ones based on modification dates.
    """

    def __init__(self):
        """Initialize NVD worker."""
        self.api_url = config.nvd_api_url
        self.api_key = config.nvd_api_key
        self.page_size = config.nvd_results_per_request
        self.timeout = config.timeout_seconds
        self.max_retries = config.max_retries

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        after=after_log(logger, logging.WARNING),
    )
    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        start_index: int,
        last_modified_start: Optional[datetime] = None,
    ) -> dict:
        """Fetch a single page of CVEs from NVD API.
        
        Args:
            client: Async HTTP client
            start_index: Pagination index
            last_modified_start: Only fetch CVEs modified after this date
            
        Returns:
            API response dict
            
        Raises:
            httpx.RequestError: On network/timeout errors (retried)
            httpx.HTTPStatusError: On 4xx/5xx responses
        """
        params = {
            "resultsPerPage": self.page_size,
            "startIndex": start_index,
        }

        # Filter by modification date if provided
        if last_modified_start:
            params["lastModStartDate"] = last_modified_start.isoformat()

        # Add optional API key if configured
        if self.api_key:
            params["apiKey"] = self.api_key

        response = await client.get(
            self.api_url, params=params, timeout=self.timeout
        )
        response.raise_for_status()

        data = response.json()
        logger.debug(
            f"Fetched {len(data.get('vulnerabilities', []))} CVEs from NVD "
            f"(start_index={start_index})"
        )
        return data

    async def _parse_cve_record(self, vuln_item: dict) -> CVERecord:
        """Parse CVE record from NVD API response.
        
        Args:
            vuln_item: CVE record from NVD API response
            
        Returns:
            CVERecord model instance
        """
        cve = vuln_item.get("cve", {})
        metrics = vuln_item.get("metrics", {})

        cve_id = cve.get("id", "")
        description = ""

        # Extract English description
        descriptions = cve.get("descriptions", [])
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break

        # Extract CVSS v3.1 score
        cvss_score = None
        cvss_vector = None
        if "cvssV31" in metrics:
            cvss_v31 = metrics["cvssV31"]
            if "cvssData" in cvss_v31:
                cvss_score = cvss_v31["cvssData"].get("baseScore")
                cvss_vector = cvss_v31["cvssData"].get("vectorString")

        # Extract CWE IDs
        cwe_ids = []
        weaknesses = cve.get("weaknesses", [])
        for weakness in weaknesses:
            for cwe in weakness.get("description", []):
                cwe_value = cwe.get("value", "")
                if cwe_value and cwe_value not in cwe_ids:
                    cwe_ids.append(cwe_value)

        # Extract affected CPEs
        affected_cpes = []
        configurations = cve.get("configurations", [])
        for config_item in configurations:
            for node in config_item.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    cpe_uri = cpe_match.get("criteria", "")
                    if cpe_uri and cpe_uri not in affected_cpes:
                        affected_cpes.append(cpe_uri)

        # Parse dates
        published_date = datetime.fromisoformat(
            cve.get("published", "").replace("Z", "+00:00")
        )
        modified_date = datetime.fromisoformat(
            cve.get("lastModified", "").replace("Z", "+00:00")
        )

        return CVERecord(
            cve_id=cve_id,
            description=description[:2000],  # Truncate to DB field size
            cvss_score=cvss_score,
            cvss_vector=cvss_vector,
            cwe_ids=cwe_ids,
            affected_cpes=affected_cpes,
            published_date=published_date,
            modified_date=modified_date,
            patch_available=False,  # Will be populated by stack matcher
        )

    async def _upsert_cve_records(
        self, session: AsyncSession, records: list[CVERecord]
    ) -> int:
        """Insert or update CVE records in database.
        
        Args:
            session: Async DB session
            records: List of CVERecord instances
            
        Returns:
            Number of records inserted/updated
        """
        for record in records:
            # Check if exists
            result = await session.execute(
                select(CVERecord).where(CVERecord.cve_id == record.cve_id)
            )
            existing = result.scalars().first()

            if existing:
                # Update if modified date is newer
                if record.modified_date > existing.modified_date:
                    existing.description = record.description
                    existing.cvss_score = record.cvss_score
                    existing.cvss_vector = record.cvss_vector
                    existing.cwe_ids = record.cwe_ids
                    existing.affected_cpes = record.affected_cpes
                    existing.modified_date = record.modified_date
                    logger.debug(f"Updated CVE {record.cve_id}")
            else:
                # Insert new
                session.add(record)
                logger.debug(f"Inserted CVE {record.cve_id}")

        await session.commit()
        return len(records)

    async def poll(self) -> dict:
        """Poll NVD API for new CVE records.
        
        Fetches all CVEs modified in the last polling interval and stores them.
        
        Returns:
            Summary dict with keys:
                - total_fetched: Total CVE records fetched
                - total_stored: Total records inserted/updated
                - next_poll_time: Next scheduled poll
                - errors: List of error messages
        """
        logger.info(f"Starting NVD poll at {datetime.now(timezone.utc)}")

        summary = {
            "total_fetched": 0,
            "total_stored": 0,
            "next_poll_time": (
                datetime.now(timezone.utc)
                + timedelta(hours=config.nvd_poll_interval_hours)
            ).isoformat(),
            "errors": [],
        }

        # Calculate date range: from (now - poll_interval) to now
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(hours=config.nvd_poll_interval_hours)

        try:
            async with httpx.AsyncClient() as client:
                start_index = 0
                all_records = []

                while True:
                    try:
                        page_data = await self._fetch_page(
                            client, start_index, last_modified_start=start_date
                        )

                        vulnerabilities = page_data.get("vulnerabilities", [])
                        if not vulnerabilities:
                            break

                        summary["total_fetched"] += len(vulnerabilities)

                        # Parse records
                        for vuln_item in vulnerabilities:
                            try:
                                record = await self._parse_cve_record(vuln_item)
                                all_records.append(record)
                            except Exception as e:
                                error_msg = (
                                    f"Failed to parse CVE: {str(e)}"
                                )
                                logger.error(error_msg)
                                summary["errors"].append(error_msg)

                        # Check if there are more pages
                        total_results = page_data.get("totalResults", 0)
                        if start_index + self.page_size >= total_results:
                            break

                        start_index += self.page_size

                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 404:
                            # No results for this date range
                            logger.info("No new CVEs found in date range")
                            break
                        raise

            # Store records in database
            if all_records:
                engine = await get_engine()
                async with async_session_factory() as session:
                    stored_count = await self._upsert_cve_records(
                        session, all_records
                    )
                    summary["total_stored"] = stored_count

            logger.info(
                f"NVD poll completed: {summary['total_fetched']} fetched, "
                f"{summary['total_stored']} stored"
            )

        except Exception as e:
            error_msg = f"NVD poll failed: {str(e)}"
            logger.error(error_msg)
            summary["errors"].append(error_msg)

        return summary


async def run_nvd_worker():
    """Run NVD worker poll cycle."""
    worker = NVDWorker()
    return await worker.poll()
