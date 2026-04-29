"""Vulnerability chain detection engine.

Detects multi-hop attack paths where multiple CVEs combine to create a more
severe attack vector than any individual CVE alone, using CWE prerequisite
graph traversal.
"""

import logging
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CVERecord, SMBStack, StackVulnerability, VulnChain
from data.cwe_graph.prerequisites import get_prerequisites

logger = logging.getLogger(__name__)

# Chain detection parameters
MIN_CHAIN_LENGTH = 2  # Minimum CVEs in a chain
MAX_CHAIN_LENGTH = 5  # Maximum depth to search (performance)
CHAIN_SCORE_THRESHOLD = 70.0  # Flag as CRITICAL if >= this


class ChainDetector:
    """Vulnerability chain detection engine.
    
    Uses CWE prerequisite graph traversal to find multi-hop attack paths
    where combining multiple CVEs creates a more severe attack outcome
    than any individual vulnerability.
    """

    def __init__(self):
        """Initialize chain detector."""
        self.min_chain_length = MIN_CHAIN_LENGTH
        self.max_chain_length = MAX_CHAIN_LENGTH
        self.score_threshold = CHAIN_SCORE_THRESHOLD

    async def _get_cves_for_stack(
        self, session: AsyncSession, stack_id: str
    ) -> dict[str, CVERecord]:
        """Fetch all CVEs matched to a stack.
        
        Args:
            session: Async DB session
            stack_id: Stack ID
            
        Returns:
            Dict mapping CVE ID to CVERecord
        """
        result = await session.execute(
            select(CVERecord)
            .join(StackVulnerability)
            .where(StackVulnerability.stack_id == stack_id)
        )
        cves = result.scalars().all()
        return {cve.cve_id: cve for cve in cves}

    async def _get_cwe_to_cves(
        self, session: AsyncSession, stack_id: str
    ) -> dict[str, list[str]]:
        """Build mapping from CWE ID to CVEs in stack.
        
        Args:
            session: Async DB session
            stack_id: Stack ID
            
        Returns:
            Dict mapping CWE ID to list of CVE IDs
        """
        cves = await self._get_cves_for_stack(session, stack_id)
        cwe_to_cves = {}

        for cve in cves.values():
            for cwe in cve.cwe_ids or []:
                if cwe not in cwe_to_cves:
                    cwe_to_cves[cwe] = []
                cwe_to_cves[cwe].append(cve.cve_id)

        return cwe_to_cves

    def _dfs_find_chains(
        self,
        start_cwe: str,
        cwe_to_cves: dict[str, list[str]],
        visited_cwes: set[str],
        current_path: list[str],
        current_cves: list[str],
        all_chains: list[dict],
    ) -> None:
        """Depth-first search to find CWE prerequisite chains.
        
        Recursively traverses the CWE prerequisite graph to find paths
        where all component CVEs exist in the stack.
        
        Args:
            start_cwe: Current CWE being explored
            cwe_to_cves: Mapping of CWEs to CVEs in stack
            visited_cwes: Set of already visited CWEs (cycle prevention)
            current_path: List of CWEs in current path
            current_cves: List of CVEs in current path
            all_chains: Accumulator for found chains
        """
        # Prevent infinite recursion
        if len(current_path) >= self.max_chain_length:
            return

        # Get CWEs this one enables
        next_cwes = get_prerequisites(start_cwe)

        for next_cwe in next_cwes:
            if next_cwe in visited_cwes:
                continue  # Avoid cycles

            # Check if this CWE has CVEs in the stack
            if next_cwe not in cwe_to_cves:
                continue

            new_visited = visited_cwes | {next_cwe}
            new_path = current_path + [next_cwe]
            new_cves = current_cves + cwe_to_cves[next_cwe]

            # Record chain if length >= minimum
            if len(new_path) >= self.min_chain_length:
                all_chains.append(
                    {
                        "cwe_path": new_path,
                        "cves": list(set(new_cves)),  # Remove duplicates
                    }
                )

            # Continue recursion
            self._dfs_find_chains(
                next_cwe,
                cwe_to_cves,
                new_visited,
                new_path,
                new_cves,
                all_chains,
            )

    def _score_chain(
        self,
        cves: list[CVERecord],
        cwe_path: list[str],
    ) -> float:
        """Score a vulnerability chain.
        
        Formula:
            chain_score = max(CVSS in chain)
                        × amplification_factor (1.5 for 2-hop, 2.0 for 3+)
                        × max(EPSS in chain)
                        × kev_bonus (1.3 if any CVE is KEV, else 1.0)
        
        Args:
            cves: List of CVERecord instances in chain
            cwe_path: List of CWEs in chain
            
        Returns:
            Composite chain score (0-100 scale)
        """
        if not cves:
            return 0.0

        # Max CVSS
        max_cvss = max([c.cvss_score or 0 for c in cves]) or 5.0
        max_cvss = min(max_cvss, 10.0)  # Cap at 10

        # Amplification factor based on chain length
        chain_length = len(cwe_path)
        if chain_length == 2:
            amplification = 1.5
        elif chain_length == 3:
            amplification = 1.8
        else:
            amplification = 2.0

        # Max EPSS
        max_epss = max([c.epss_score or 0 for c in cves]) or 0.5
        max_epss = min(max_epss, 1.0)  # Cap at 1

        # KEV bonus
        kev_bonus = 1.3 if any(c.is_kev for c in cves) else 1.0

        # Final score (normalized to 0-100)
        score = (max_cvss / 10.0) * amplification * max_epss * kev_bonus * 100
        return min(score, 100.0)

    def _attack_outcome_from_path(self, cwe_path: list[str]) -> str:
        """Infer likely attack outcome from CWE chain.
        
        Args:
            cwe_path: List of CWEs in chain
            
        Returns:
            Expected outcome (RCE, PRIVESC, EXFIL, etc.)
        """
        # Simple heuristic: look at final CWE in path
        if not cwe_path:
            return "UNKNOWN"

        final_cwe = cwe_path[-1]

        if final_cwe in ["CWE-427", "CWE-94"]:
            return "RCE"  # Code Execution
        elif final_cwe in ["CWE-269"]:
            return "PRIVESC"  # Privilege Escalation
        elif final_cwe in ["CWE-200"]:
            return "EXFIL"  # Information Disclosure/Exfiltration
        elif final_cwe in ["CWE-276", "CWE-287"]:
            return "AUTH_BYPASS"
        else:
            return "CHAIN_ATTACK"

    async def detect_chains(
        self,
        session: AsyncSession,
        stack: SMBStack,
    ) -> dict:
        """Detect vulnerability chains for an SMB stack.
        
        Performs CWE graph traversal to find multi-hop attack paths where
        multiple CVEs in the stack's tech stack combine to amplify risk.
        
        Args:
            session: Async DB session
            stack: SMBStack instance
            
        Returns:
            Summary dict with:
                - chains_found: Number of chains detected
                - critical_chains: Chains with score >= threshold
                - stored_count: Chains persisted to DB
                - errors: List of error messages
        """
        logger.info(f"Starting chain detection for {stack.org_name}")

        summary = {
            "chains_found": 0,
            "critical_chains": 0,
            "stored_count": 0,
            "errors": [],
        }

        try:
            # Build CWE-to-CVE mapping for stack
            cwe_to_cves = await self._get_cwe_to_cves(session, stack.id)

            if not cwe_to_cves:
                logger.debug(f"No CVEs found for {stack.org_name}, skipping chain detection")
                return summary

            # Fetch all CVEs for scoring
            cves_by_id = await self._get_cves_for_stack(session, stack.id)

            # Find all chains
            all_chains = []
            for start_cwe in cwe_to_cves.keys():
                self._dfs_find_chains(
                    start_cwe,
                    cwe_to_cves,
                    {start_cwe},
                    [start_cwe],
                    cwe_to_cves[start_cwe],
                    all_chains,
                )

            summary["chains_found"] = len(all_chains)
            logger.debug(f"Found {len(all_chains)} potential chains")

            # Score and store chains
            chains_to_store = []
            for chain_data in all_chains:
                cwe_path = chain_data["cwe_path"]
                cve_ids = chain_data["cves"]

                # Get CVE records for scoring
                chain_cves = [cves_by_id[cve_id] for cve_id in cve_ids if cve_id in cves_by_id]

                if not chain_cves:
                    continue

                # Score chain
                chain_score = self._score_chain(chain_cves, cwe_path)

                # Only store high-scoring chains or very long paths
                if chain_score >= 50.0 or len(cwe_path) >= 3:
                    chain = VulnChain(
                        stack_id=stack.id,
                        cve_ids=cve_ids,
                        cwe_path=cwe_path,
                        chain_score=chain_score,
                        attack_outcome=self._attack_outcome_from_path(cwe_path),
                    )
                    chains_to_store.append(chain)

                    if chain_score >= self.score_threshold:
                        summary["critical_chains"] += 1

            # Persist chains
            if chains_to_store:
                session.add_all(chains_to_store)
                await session.commit()
                summary["stored_count"] = len(chains_to_store)

            logger.info(
                f"Chain detection complete: {summary['chains_found']} found, "
                f"{summary['stored_count']} stored, "
                f"{summary['critical_chains']} critical"
            )

        except Exception as e:
            error_msg = f"Chain detection failed: {str(e)}"
            logger.error(error_msg)
            summary["errors"].append(error_msg)
            await session.rollback()

        return summary
