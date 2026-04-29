"""CPE-based vulnerability matching engine.

Matches declared SMB stack CPEs against known CVE impact data to identify
which vulnerabilities affect a specific organization's infrastructure.
"""

import logging
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CVERecord, SMBStack, StackVulnerability

logger = logging.getLogger(__name__)


class StackMatcher:
    """CPE-based stack-to-vulnerability matcher.
    
    Compares an SMB's declared tech stack (CPE identifiers) against
    CVE records to identify applicable vulnerabilities.
    """

    @staticmethod
    def _normalize_cpe(cpe: str) -> str:
        """Normalize CPE string for comparison.
        
        Removes version wildcards and trailing colons for fuzzy matching.
        
        Args:
            cpe: CPE string (e.g., "cpe:2.3:a:apache:log4j:2.17.0:*:*:*:*:*:*:*")
            
        Returns:
            Normalized CPE for matching
        """
        # Remove trailing wildcards
        while cpe.endswith(":*"):
            cpe = cpe[:-2]
        return cpe.rstrip(":")

    @staticmethod
    def _cpe_matches(declared_cpe: str, affected_cpe: str) -> bool:
        """Check if a CVE's affected CPE matches SMB's declared CPE.
        
        Performs both exact and prefix matching to handle version wildcards.
        
        Args:
            declared_cpe: CPE from SMB stack declaration
            affected_cpe: CPE from CVE record
            
        Returns:
            True if they match (exact or prefix)
        """
        norm_declared = StackMatcher._normalize_cpe(declared_cpe)
        norm_affected = StackMatcher._normalize_cpe(affected_cpe)

        # Exact match
        if norm_declared == norm_affected:
            return True

        # Prefix match (for major.minor version matching)
        # e.g., "apache:log4j:2" matches "apache:log4j:2.17.0"
        if norm_declared in norm_affected or norm_affected in norm_declared:
            return True

        return False

    async def match_stack_to_cves(
        self,
        session: AsyncSession,
        stack: SMBStack,
    ) -> dict:
        """Match an SMB stack to applicable CVEs.
        
        Queries all CVE records and checks if their affected CPEs match
        the stack's declared CPEs. Creates StackVulnerability records.
        
        Args:
            session: Async DB session
            stack: SMBStack instance to match
            
        Returns:
            Summary dict with:
                - matched_count: Number of matches created
                - errors: List of error messages
        """
        logger.info(f"Starting stack match for {stack.org_name} ({stack.id})")

        summary = {
            "matched_count": 0,
            "errors": [],
        }

        try:
            # Fetch all CVE records
            result = await session.execute(select(CVERecord))
            all_cves = result.scalars().all()

            logger.debug(f"Checking {len(all_cves)} CVEs against stack CPEs")

            matches_to_add = []

            # Check each CVE against stack CPEs
            for cve in all_cves:
                for affected_cpe in cve.affected_cpes or []:
                    for declared_cpe in stack.cpe_identifiers or []:
                        if self._cpe_matches(declared_cpe, affected_cpe):
                            # Create match record
                            existing = await session.execute(
                                select(StackVulnerability).where(
                                    and_(
                                        StackVulnerability.stack_id == stack.id,
                                        StackVulnerability.cve_id == cve.cve_id,
                                    )
                                )
                            )

                            if not existing.scalars().first():
                                match = StackVulnerability(
                                    stack_id=stack.id,
                                    cve_id=cve.cve_id,
                                    priority_score=0.0,  # Will be set by prioritizer
                                    priority_label="UNSCORED",
                                )
                                matches_to_add.append(match)
                                logger.debug(
                                    f"Matched {cve.cve_id} to {stack.org_name}"
                                )
                            break  # One match per CVE per stack is enough

            # Bulk add
            session.add_all(matches_to_add)
            await session.commit()

            summary["matched_count"] = len(matches_to_add)
            logger.info(
                f"Stack match complete: {summary['matched_count']} vulnerabilities found"
            )

        except Exception as e:
            error_msg = f"Stack matching failed: {str(e)}"
            logger.error(error_msg)
            summary["errors"].append(error_msg)
            await session.rollback()

        return summary

    async def match_new_cve(
        self,
        session: AsyncSession,
        cve: CVERecord,
    ) -> dict:
        """Match a newly ingested CVE against all registered stacks.
        
        Called when a new CVE is ingested to immediately flag affected stacks.
        
        Args:
            session: Async DB session
            cve: New CVERecord to match
            
        Returns:
            Summary dict with match count
        """
        logger.debug(f"Matching new CVE {cve.cve_id} against all stacks")

        summary = {"matched_stacks": 0, "errors": []}

        try:
            # Fetch all stacks
            result = await session.execute(select(SMBStack))
            all_stacks = result.scalars().all()

            matches_to_add = []

            for stack in all_stacks:
                for affected_cpe in cve.affected_cpes or []:
                    for declared_cpe in stack.cpe_identifiers or []:
                        if self._cpe_matches(declared_cpe, affected_cpe):
                            # Check if already exists
                            existing = await session.execute(
                                select(StackVulnerability).where(
                                    and_(
                                        StackVulnerability.stack_id == stack.id,
                                        StackVulnerability.cve_id == cve.cve_id,
                                    )
                                )
                            )

                            if not existing.scalars().first():
                                match = StackVulnerability(
                                    stack_id=stack.id,
                                    cve_id=cve.cve_id,
                                    priority_score=0.0,
                                    priority_label="UNSCORED",
                                )
                                matches_to_add.append(match)
                            break

            session.add_all(matches_to_add)
            await session.commit()

            summary["matched_stacks"] = len(matches_to_add)
            logger.info(
                f"New CVE {cve.cve_id} matched to {summary['matched_stacks']} stacks"
            )

        except Exception as e:
            error_msg = f"CVE matching failed: {str(e)}"
            logger.error(error_msg)
            summary["errors"].append(error_msg)
            await session.rollback()

        return summary
