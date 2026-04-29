"""FIRST EPSS (Exploit Prediction Scoring System) worker.

Fetches EPSS scores from FIRST.org API and updates CVE records with exploit
probability predictions.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.database.connection import get_engine, async_session_factory
from backend.database.models import CVERecord
from backend.ingestion.config import config

logger = logging.getLogger(__name__)


class EPSSWorker:
    """FIRST EPSS score fetching worker.
    
    Fetches exploit prediction scores from FIRST.org API and updates
    CVE records with EPSS probability and percentile data.
    """

    def __init__(self):
        """Initialize EPSS worker."""
        self.api_url = config.epss_api_url
        self.page_size = config.epss_page_size
        self.timeout = config.timeout_seconds

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        after=after_log(logger, logging.WARNING),
    )
    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        skip: int,
    ) -> dict:
        """Fetch a single page of EPSS scores.
        
        Args:
            client: Async HTTP client
            skip: Number of records to skip (pagination)
            
        Returns:
            API response dict
            
        Raises:
            httpx.RequestError: On network/timeout errors (retried)
            httpx.HTTPStatusError: On 4xx/5xx responses
        """
        params = {
            "skip": skip,
            "limit": self.page_size,
        }

        response = await client.get(
            self.api_url, params=params, timeout=self.timeout
        )
        response.raise_for_status()

        data = response.json()
        logger.debug(
            f"Fetched {len(data.get('data', []))} EPSS scores "
            f"(skip={skip})"
        )
        return data

    async def _upsert_epss_scores(
        self, session: AsyncSession, score_dict: dict[str, dict]
    ) -> int:
        """Update CVE records with EPSS scores.
        
        Args:
            session: Async DB session
            score_dict: Dict mapping CVE IDs to EPSS scores
                Format: {
                    "CVE-2024-12345": {
                        "epss": 0.95,
                        "percentile": 0.98
                    },
                    ...
                }
            
        Returns:
            Number of records updated
        """
        if not score_dict:
            return 0

        updated_count = 0

        for cve_id, scores in score_dict.items():
            stmt = (
                update(CVERecord)
                .where(CVERecord.cve_id == cve_id)
                .values(
                    epss_score=scores.get("epss"),
                    epss_percentile=scores.get("percentile"),
                )
            )
            result = await session.execute(stmt)
            if result.rowcount > 0:
                updated_count += result.rowcount
                logger.debug(
                    f"Updated EPSS for {cve_id}: "
                    f"score={scores.get('epss')}, "
                    f"percentile={scores.get('percentile')}"
                )

        await session.commit()
        return updated_count

    async def fetch(self) -> dict:
        """Fetch all EPSS scores and update database.
        
        Paginates through FIRST EPSS API and stores scores in CVE records.
        
        Returns:
            Summary dict with keys:
                - total_fetched: Total EPSS records fetched
                - total_updated: Total CVE records updated
                - next_fetch_time: Next scheduled fetch
                - errors: List of error messages
        """
        logger.info(f"Starting EPSS fetch at {datetime.now(timezone.utc)}")

        summary = {
            "total_fetched": 0,
            "total_updated": 0,
            "next_fetch_time": (
                datetime.now(timezone.utc)
                + timedelta(hours=config.epss_poll_interval_hours)
            ).isoformat(),
            "errors": [],
        }

        try:
            all_scores = {}

            async with httpx.AsyncClient() as client:
                skip = 0

                while True:
                    try:
                        page_data = await self._fetch_page(client, skip)

                        epss_data = page_data.get("data", [])
                        if not epss_data:
                            break

                        summary["total_fetched"] += len(epss_data)

                        # Parse scores
                        for entry in epss_data:
                            cve_id = entry.get("cve")
                            epss = entry.get("epss")
                            percentile = entry.get("percentile")

                            if cve_id and epss is not None:
                                all_scores[cve_id] = {
                                    "epss": float(epss),
                                    "percentile": float(percentile)
                                    if percentile is not None
                                    else None,
                                }

                        # Check if there are more pages
                        total = page_data.get("total", 0)
                        if skip + self.page_size >= total:
                            break

                        skip += self.page_size

                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 404:
                            logger.info("No more EPSS data available")
                            break
                        raise

            # Update database
            if all_scores:
                engine = await get_engine()
                async with async_session_factory() as session:
                    updated = await self._upsert_epss_scores(
                        session, all_scores
                    )
                    summary["total_updated"] = updated

            logger.info(
                f"EPSS fetch completed: {summary['total_fetched']} fetched, "
                f"{summary['total_updated']} updated"
            )

        except Exception as e:
            error_msg = f"EPSS fetch failed: {str(e)}"
            logger.error(error_msg)
            summary["errors"].append(error_msg)

        return summary


async def run_epss_worker():
    """Run EPSS worker fetch cycle."""
    worker = EPSSWorker()
    return await worker.fetch()
