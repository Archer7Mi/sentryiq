"""FastAPI routes for AI-powered intelligence.

Endpoints for generating plain-English alerts, chain narratives,
and phishing simulations using NVIDIA NIM.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.nim_client import NIMClient
from ai.schemas import (
    StackVulnerabilityAlert,
    VulnerabilityChainAlert,
)
from database.connection import get_db_session
from database.models import (
    CVERecord,
    SMBStack,
    StackVulnerability,
    VulnChain,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Global NIM client (initialized on startup)
nim_client: Optional[NIMClient] = None


def get_nim_client() -> NIMClient:
    """Get global NIM client instance.
    
    Raises:
        RuntimeError: If client not initialized
    """
    if nim_client is None:
        raise RuntimeError("NIM client not initialized")
    return nim_client


async def init_nim_client():
    """Initialize NIM client on app startup."""
    global nim_client
    try:
        nim_client = NIMClient()
        logger.info("NIM client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize NIM client: {e}")
        raise


async def shutdown_nim_client():
    """Close NIM client on app shutdown."""
    global nim_client
    if nim_client:
        await nim_client.close()
        logger.info("NIM client closed")


@router.post("/vulnerabilities/{stack_id}/synthesize")
async def synthesize_stack_alerts(
    stack_id: str,
    session: AsyncSession = Depends(get_db_session),
    nim: NIMClient = Depends(get_nim_client),
) -> dict:
    """Generate plain-English alerts for all vulnerabilities in a stack.
    
    Fetches unalerted vulnerabilities, calls NIM for synthesis,
    updates database with alert text and remediation steps.
    
    Args:
        stack_id: Stack UUID
        session: DB session
        nim: NIM client
        
    Returns:
        Summary of alerts generated
    """
    logger.info(f"Synthesizing alerts for stack {stack_id}")

    try:
        # Verify stack exists
        result = await session.execute(
            select(SMBStack).where(SMBStack.id == stack_id)
        )
        stack = result.scalars().first()

        if not stack:
            raise HTTPException(status_code=404, detail="Stack not found")

        # Fetch vulnerabilities without alerts
        vuln_result = await session.execute(
            select(StackVulnerability).where(
                StackVulnerability.stack_id == stack_id,
                StackVulnerability.plain_english_alert.is_(None),
            )
        )
        vulns_to_alert = vuln_result.scalars().all()

        if not vulns_to_alert:
            return {
                "stack_id": stack_id,
                "alerts_generated": 0,
                "message": "No unalerted vulnerabilities",
            }

        alerts_generated = 0

        for vuln in vulns_to_alert:
            try:
                # Get CVE data
                cve_result = await session.execute(
                    select(CVERecord).where(CVERecord.cve_id == vuln.cve_id)
                )
                cve = cve_result.scalars().first()

                if not cve:
                    logger.warning(f"CVE not found: {vuln.cve_id}")
                    continue

                # Get affected systems from stack
                affected_systems = [
                    cpe for cpe in stack.cpe_identifiers
                    if any(cpe in affected_cpe for affected_cpe in cve.affected_cpes)
                ]

                # Synthesize alert
                nim_response = await nim.synthesize_cve(
                    cve_id=cve.cve_id,
                    description=cve.description,
                    cvss_score=cve.cvss_score,
                    affected_systems=affected_systems or cve.affected_cpes[:3],
                )

                # Update database
                vuln.plain_english_alert = nim_response.get("alert", "")
                vuln.remediation_steps = nim_response.get("remediation", "")

                alerts_generated += 1
                logger.debug(f"Generated alert for {cve.cve_id}")

            except Exception as e:
                logger.error(f"Failed to synthesize alert for {vuln.cve_id}: {e}")
                continue

        await session.commit()

        return {
            "stack_id": stack_id,
            "alerts_generated": alerts_generated,
            "total_vulnerabilities": len(vulns_to_alert),
        }

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chains/{stack_id}/analyze")
async def analyze_chain_narratives(
    stack_id: str,
    session: AsyncSession = Depends(get_db_session),
    nim: NIMClient = Depends(get_nim_client),
) -> dict:
    """Generate narratives for detected vulnerability chains.
    
    Fetches chains without narratives, calls NIM for analysis,
    updates database.
    
    Args:
        stack_id: Stack UUID
        session: DB session
        nim: NIM client
        
    Returns:
        Summary of chains analyzed
    """
    logger.info(f"Analyzing chains for stack {stack_id}")

    try:
        # Verify stack exists
        result = await session.execute(
            select(SMBStack).where(SMBStack.id == stack_id)
        )
        stack = result.scalars().first()

        if not stack:
            raise HTTPException(status_code=404, detail="Stack not found")

        # Fetch chains without narratives
        chain_result = await session.execute(
            select(VulnChain).where(
                VulnChain.stack_id == stack_id,
                VulnChain.chain_narrative.is_(None),
            )
        )
        chains_to_analyze = chain_result.scalars().all()

        if not chains_to_analyze:
            return {
                "stack_id": stack_id,
                "chains_analyzed": 0,
                "message": "No chains to analyze",
            }

        chains_analyzed = 0

        for chain in chains_to_analyze:
            try:
                # Analyze chain
                nim_response = await nim.analyze_chain(
                    cve_ids=chain.cve_ids or [],
                    cwe_path=chain.cwe_path or [],
                    attack_description=f"Attack leads to {chain.attack_outcome}",
                )

                # Update database
                chain.chain_narrative = nim_response.get("narrative", "")

                chains_analyzed += 1
                logger.debug(f"Generated narrative for chain {chain.id}")

            except Exception as e:
                logger.error(f"Failed to analyze chain {chain.id}: {e}")
                continue

        await session.commit()

        return {
            "stack_id": stack_id,
            "chains_analyzed": chains_analyzed,
            "total_chains": len(chains_to_analyze),
        }

    except Exception as e:
        logger.error(f"Chain analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vulnerabilities/{stack_id}")
async def get_stack_alerts(
    stack_id: str,
    priority: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get all vulnerability alerts for a stack.
    
    Args:
        stack_id: Stack UUID
        priority: Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)
        session: DB session
        
    Returns:
        List of StackVulnerabilityAlert
    """
    logger.debug(f"Fetching alerts for stack {stack_id}")

    try:
        # Verify stack exists
        result = await session.execute(
            select(SMBStack).where(SMBStack.id == stack_id)
        )
        stack = result.scalars().first()

        if not stack:
            raise HTTPException(status_code=404, detail="Stack not found")

        # Fetch vulnerabilities
        query = select(StackVulnerability).where(
            StackVulnerability.stack_id == stack_id,
        )

        if priority:
            query = query.where(StackVulnerability.priority_label == priority)

        vuln_result = await session.execute(query)
        vulns = vuln_result.scalars().all()

        # Format response
        alerts = []
        for vuln in vulns:
            alert = StackVulnerabilityAlert(
                cve_id=vuln.cve_id,
                priority_label=vuln.priority_label,
                priority_score=float(vuln.priority_score),
                plain_english_alert=vuln.plain_english_alert or "",
                remediation_steps=vuln.remediation_steps or "",
                is_part_of_chain=vuln.chain_id is not None,
            )
            alerts.append(alert)

        return {
            "stack_id": stack_id,
            "total_alerts": len(alerts),
            "alerts": alerts,
        }

    except Exception as e:
        logger.error(f"Failed to fetch alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chains/{stack_id}")
async def get_chain_alerts(
    stack_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get all vulnerability chain alerts for a stack.
    
    Args:
        stack_id: Stack UUID
        session: DB session
        
    Returns:
        List of VulnerabilityChainAlert
    """
    logger.debug(f"Fetching chains for stack {stack_id}")

    try:
        # Verify stack exists
        result = await session.execute(
            select(SMBStack).where(SMBStack.id == stack_id)
        )
        stack = result.scalars().first()

        if not stack:
            raise HTTPException(status_code=404, detail="Stack not found")

        # Fetch chains
        chain_result = await session.execute(
            select(VulnChain).where(VulnChain.stack_id == stack_id)
        )
        chains = chain_result.scalars().all()

        # Format response
        chain_alerts = []
        for chain in chains:
            alert = VulnerabilityChainAlert(
                chain_id=str(chain.id),
                cve_ids=chain.cve_ids or [],
                chain_score=float(chain.chain_score),
                attack_outcome=chain.attack_outcome,
                chain_narrative=chain.chain_narrative or "",
            )
            chain_alerts.append(alert)

        return {
            "stack_id": stack_id,
            "total_chains": len(chain_alerts),
            "chains": chain_alerts,
        }

    except Exception as e:
        logger.error(f"Failed to fetch chains: {e}")
        raise HTTPException(status_code=500, detail=str(e))
