"""CISA Known Exploited Vulnerabilities (KEV) sync worker.

Downloads the CISA KEV JSON catalog and marks matching CVEs in database
as actively exploited.
"""

import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import update
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


class KEVWorker:
    """CISA Known Exploited Vulnerabilities sync worker.
    
    Fetches the CISA KEV catalog and updates the is_kev flag for matching CVEs
    in the database.
    """

    def __init__(self):
        """Initialize KEV worker."""
        self.kev_url = config.kev_url
        self.timeout = config.timeout_seconds

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        after=after_log(logger, logging.WARNING),
    )
    async def _fetch_kev_catalog(self, client: httpx.AsyncClient) -> dict:
        """Fetch CISA KEV JSON catalog.
        
        Args:
            client: Async HTTP client
            
        Returns:
            KEV catalog dict
            
        Raises:
            httpx.RequestError: On network/timeout errors (retried)
            httpx.HTTPStatusError: On 4xx/5xx responses
        """
        response = await client.get(self.kev_url, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"Fetched CISA KEV catalog with {len(data.get('vulnerabilities', []))} entries")
        return data

    async def _update_kev_flags(
        self, session: AsyncSession, cve_ids: list[str]
    ) -> int:
        """Update is_kev flag for CVEs in database.
        
        Args:
            session: Async DB session
            cve_ids: List of CVE IDs from KEV catalog
            
        Returns:
            Number of records updated
        """
        if not cve_ids:
            return 0

        # Update all matching CVEs
        stmt = (
            update(CVERecord)
            .where(CVERecord.cve_id.in_(cve_ids))
            .values(is_kev=True)
        )
        result = await session.execute(stmt)
        await session.commit()

        count = result.rowcount
        logger.info(f"Marked {count} CVEs as KEV (actively exploited)")
        return count

    async def sync(self) -> dict:
        """Sync CISA KEV catalog to database.
        
        Fetches the latest KEV entries and updates matching CVEs.
        
        Returns:
            Summary dict with keys:
                - kev_count: Number of CVEs in KEV catalog
                - updated_count: Number of CVEs updated in DB
                - last_sync_time: ISO timestamp of this sync
                - next_sync_time: Estimated next sync
                - errors: List of error messages
        """
        logger.info(f"Starting CISA KEV sync at {datetime.now(timezone.utc)}")

        summary = {
            "kev_count": 0,
            "updated_count": 0,
            "last_sync_time": datetime.now(timezone.utc).isoformat(),
            "next_sync_time": (
                datetime.now(timezone.utc)
                + timedelta(hours=config.kev_sync_interval_hours)
            ).isoformat(),
            "errors": [],
        }

        try:
            async with httpx.AsyncClient() as client:
                catalog = await self._fetch_kev_catalog(client)

                # Extract CVE IDs
                vulnerabilities = catalog.get("vulnerabilities", [])
                cve_ids = [v.get("cveID") for v in vulnerabilities if v.get("cveID")]

                summary["kev_count"] = len(cve_ids)

                if cve_ids:
                    # Update database
                    engine = await get_engine()
                    async with async_session_factory() as session:
                        updated = await self._update_kev_flags(session, cve_ids)
                        summary["updated_count"] = updated

            logger.info(
                f"CISA KEV sync completed: {summary['kev_count']} in catalog, "
                f"{summary['updated_count']} updated in DB"
            )

        except Exception as e:
            error_msg = f"CISA KEV sync failed: {str(e)}"
            logger.error(error_msg)
            summary["errors"].append(error_msg)

        return summary


async def run_kev_worker():
    """Run KEV worker sync cycle."""
    worker = KEVWorker()
    return await worker.sync()
