"""Vulnerability prioritization scoring engine.

Combines CVSS, EPSS, KEV status, and chain detection into a composite
priority score that ranks vulnerabilities by real-world exploitability
and business impact.
"""

import logging

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CVERecord, StackVulnerability, VulnChain

logger = logging.getLogger(__name__)

# Scoring weights and thresholds
CVSS_WEIGHT = 0.3
EPSS_WEIGHT = 0.4
KEV_WEIGHT = 0.15
CHAIN_WEIGHT = 0.15

CRITICAL_THRESHOLD = 85.0
HIGH_THRESHOLD = 65.0
MEDIUM_THRESHOLD = 40.0
# LOW = anything below MEDIUM


class Prioritizer:
    """Vulnerability prioritization engine.
    
    Calculates composite risk scores combining multiple signals:
    - CVSS (technical severity)
    - EPSS (exploit probability)
    - KEV status (known exploited)
    - Chain amplification (multi-hop attack paths)
    """

    @staticmethod
    def _calculate_base_score(cve: CVERecord) -> float:
        """Calculate base priority score from CVE metrics.
        
        Uses weighted combination of CVSS and EPSS.
        
        Args:
            cve: CVERecord instance
            
        Returns:
            Score 0-100
        """
        cvss = (cve.cvss_score or 0.0) / 10.0  # Normalize to 0-1
        epss = (cve.epss_score or 0.0)  # Already 0-1

        base_score = (cvss * CVSS_WEIGHT + epss * EPSS_WEIGHT) * 100

        return base_score

    @staticmethod
    def _apply_kev_bonus(score: float, is_kev: bool) -> float:
        """Apply known-exploited bonus to score.
        
        Args:
            score: Current score
            is_kev: Is this CVE in CISA KEV
            
        Returns:
            Updated score
        """
        if is_kev:
            # Boost by KEV weight (15% of max = 15 points)
            return min(score + 15.0, 100.0)
        return score

    @staticmethod
    def _apply_chain_bonus(
        base_score: float, 
        highest_chain_score: float
    ) -> float:
        """Apply chain detection bonus.
        
        If this CVE is part of a high-scoring chain, boost its individual priority.
        
        Args:
            base_score: Current score
            highest_chain_score: Score of best chain this CVE is in
            
        Returns:
            Updated score
        """
        if highest_chain_score > 0:
            # Blend chain score (15% weight) with base score
            blended = (
                base_score * (1.0 - CHAIN_WEIGHT)
                + highest_chain_score * CHAIN_WEIGHT
            )
            return min(blended, 100.0)
        return base_score

    @staticmethod
    def _score_to_label(score: float) -> str:
        """Convert numeric score to priority label.
        
        Args:
            score: Numeric score 0-100
            
        Returns:
            Priority label (CRITICAL, HIGH, MEDIUM, LOW)
        """
        if score >= CRITICAL_THRESHOLD:
            return "CRITICAL"
        elif score >= HIGH_THRESHOLD:
            return "HIGH"
        elif score >= MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "LOW"

    async def score_stack_vulnerabilities(
        self,
        session: AsyncSession,
        stack_id: str,
    ) -> dict:
        """Calculate and store priority scores for all vulnerabilities in stack.
        
        Processes all matched CVEs and chains, computing composite scores
        and updating StackVulnerability records.
        
        Args:
            session: Async DB session
            stack_id: Stack ID
            
        Returns:
            Summary dict with:
                - scored_count: Number of vulnerabilities scored
                - critical_count: CRITICAL priority vulns
                - high_count: HIGH priority
                - medium_count: MEDIUM priority
                - low_count: LOW priority
                - errors: List of errors
        """
        logger.info(f"Scoring vulnerabilities for stack {stack_id}")

        summary = {
            "scored_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "errors": [],
        }

        try:
            # Fetch all vulnerabilities for this stack
            vuln_result = await session.execute(
                select(StackVulnerability).where(
                    StackVulnerability.stack_id == stack_id
                )
            )
            vulns = vuln_result.scalars().all()

            # Build map of CVE ID -> highest chain score
            chain_result = await session.execute(
                select(VulnChain).where(VulnChain.stack_id == stack_id)
            )
            chains = chain_result.scalars().all()

            cve_to_best_chain = {}
            for chain in chains:
                for cve_id in chain.cve_ids or []:
                    if cve_id not in cve_to_best_chain:
                        cve_to_best_chain[cve_id] = chain.chain_score
                    else:
                        cve_to_best_chain[cve_id] = max(
                            cve_to_best_chain[cve_id], chain.chain_score
                        )

            # Score each vulnerability
            for vuln in vulns:
                try:
                    # Get CVE record
                    cve_result = await session.execute(
                        select(CVERecord).where(CVERecord.cve_id == vuln.cve_id)
                    )
                    cve = cve_result.scalars().first()

                    if not cve:
                        continue

                    # Calculate composite score
                    base_score = self._calculate_base_score(cve)
                    kev_score = self._apply_kev_bonus(base_score, cve.is_kev)
                    chain_score = cve_to_best_chain.get(cve.cve_id, 0.0)
                    final_score = self._apply_chain_bonus(kev_score, chain_score)

                    # Get label
                    label = self._score_to_label(final_score)

                    # Update vulnerability record
                    vuln.priority_score = final_score
                    vuln.priority_label = label

                    # Track summary
                    if label == "CRITICAL":
                        summary["critical_count"] += 1
                    elif label == "HIGH":
                        summary["high_count"] += 1
                    elif label == "MEDIUM":
                        summary["medium_count"] += 1
                    else:
                        summary["low_count"] += 1

                    logger.debug(
                        f"Scored {vuln.cve_id}: {final_score:.1f} ({label})"
                    )

                except Exception as e:
                    logger.error(f"Failed to score {vuln.cve_id}: {str(e)}")
                    summary["errors"].append(f"Score error for {vuln.cve_id}: {str(e)}")

            # Commit all updates
            await session.commit()
            summary["scored_count"] = len(vulns)

            logger.info(
                f"Scoring complete: {summary['critical_count']} CRITICAL, "
                f"{summary['high_count']} HIGH, "
                f"{summary['medium_count']} MEDIUM, "
                f"{summary['low_count']} LOW"
            )

        except Exception as e:
            error_msg = f"Vulnerability scoring failed: {str(e)}"
            logger.error(error_msg)
            summary["errors"].append(error_msg)
            await session.rollback()

        return summary
