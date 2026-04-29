"""FastAPI routes for phishing simulation and human risk scoring.

Endpoints for creating campaigns, tracking interactions, and computing
employee/organization risk profiles.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.nim_client import NIMClient
from backend.database.connection import get_db_session
from backend.simulation.phishing import PhishingSimulationEngine
from backend.simulation.scoring import HumanRiskScorer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/simulations", tags=["simulations"])

# Global instances
phishing_engine: Optional[PhishingSimulationEngine] = None
risk_scorer: Optional[HumanRiskScorer] = None


def get_phishing_engine() -> PhishingSimulationEngine:
    """Get phishing engine instance."""
    if phishing_engine is None:
        raise RuntimeError("Phishing engine not initialized")
    return phishing_engine


def get_risk_scorer() -> HumanRiskScorer:
    """Get risk scorer instance."""
    if risk_scorer is None:
        raise RuntimeError("Risk scorer not initialized")
    return risk_scorer


async def init_phishing_engine(nim_client: NIMClient):
    """Initialize phishing engine on app startup."""
    global phishing_engine
    try:
        phishing_engine = PhishingSimulationEngine(nim_client)
        logger.info("Phishing engine initialized")
    except Exception as e:
        logger.error(f"Failed to initialize phishing engine: {e}")
        raise


async def init_risk_scorer():
    """Initialize risk scorer on app startup."""
    global risk_scorer
    try:
        risk_scorer = HumanRiskScorer()
        logger.info("Risk scorer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize risk scorer: {e}")
        raise


@router.post("/campaigns/create")
async def create_campaign(
    stack_id: str,
    campaign_type: str,
    target_employee_role: str,
    company_name: str,
    session: AsyncSession = Depends(get_db_session),
    engine: PhishingSimulationEngine = Depends(get_phishing_engine),
) -> dict:
    """Create a phishing simulation campaign.

    Args:
        stack_id: Target organization stack
        campaign_type: 'phishing', 'vishing', 'smishing'
        target_employee_role: e.g., 'HR', 'Finance', 'IT'
        company_name: Organization name
        session: DB session
        engine: Phishing engine

    Returns:
        Campaign details with generated email content
    """
    logger.info(f"Creating campaign for stack {stack_id}")

    try:
        result = await engine.create_campaign(
            session,
            stack_id,
            campaign_type,
            target_employee_role,
            company_name,
        )
        return result
    except Exception as e:
        logger.error(f"Campaign creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/campaigns/{campaign_id}/launch")
async def launch_campaign(
    campaign_id: str,
    target_employee_ids: list[str],
    session: AsyncSession = Depends(get_db_session),
    engine: PhishingSimulationEngine = Depends(get_phishing_engine),
) -> dict:
    """Launch a campaign to target employees.

    Args:
        campaign_id: Campaign UUID
        target_employee_ids: List of hashed employee IDs
        session: DB session
        engine: Phishing engine

    Returns:
        Launch summary
    """
    logger.info(f"Launching campaign {campaign_id}")

    try:
        result = await engine.launch_campaign(session, campaign_id, target_employee_ids)
        return result
    except Exception as e:
        logger.error(f"Campaign launch failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/interactions/click")
async def record_click(
    campaign_id: str,
    employee_id: str,
    session: AsyncSession = Depends(get_db_session),
    engine: PhishingSimulationEngine = Depends(get_phishing_engine),
) -> dict:
    """Record employee click on phishing link.

    Args:
        campaign_id: Campaign UUID
        employee_id: Hashed employee identifier
        session: DB session
        engine: Phishing engine

    Returns:
        Updated risk score
    """
    logger.debug(f"Recording click: {campaign_id}, {employee_id}")

    try:
        result = await engine.record_click(session, campaign_id, employee_id)
        return result
    except Exception as e:
        logger.error(f"Click recording failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/interactions/report")
async def record_report(
    campaign_id: str,
    employee_id: str,
    session: AsyncSession = Depends(get_db_session),
    engine: PhishingSimulationEngine = Depends(get_phishing_engine),
) -> dict:
    """Record employee report of phishing email.

    Args:
        campaign_id: Campaign UUID
        employee_id: Hashed employee identifier
        session: DB session
        engine: Phishing engine

    Returns:
        Updated risk score
    """
    logger.debug(f"Recording report: {campaign_id}, {employee_id}")

    try:
        result = await engine.record_report(session, campaign_id, employee_id)
        return result
    except Exception as e:
        logger.error(f"Report recording failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/campaigns/{campaign_id}/complete")
async def complete_campaign(
    campaign_id: str,
    session: AsyncSession = Depends(get_db_session),
    engine: PhishingSimulationEngine = Depends(get_phishing_engine),
) -> dict:
    """Mark campaign as completed.

    Args:
        campaign_id: Campaign UUID
        session: DB session
        engine: Phishing engine

    Returns:
        Campaign summary
    """
    logger.info(f"Completing campaign {campaign_id}")

    try:
        result = await engine.complete_campaign(session, campaign_id)
        return result
    except Exception as e:
        logger.error(f"Campaign completion failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: str,
    session: AsyncSession = Depends(get_db_session),
    engine: PhishingSimulationEngine = Depends(get_phishing_engine),
) -> dict:
    """Get statistics for a campaign.

    Args:
        campaign_id: Campaign UUID
        session: DB session
        engine: Phishing engine

    Returns:
        Campaign statistics
    """
    try:
        result = await engine.get_campaign_stats(session, campaign_id)
        return result
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/risk/{stack_id}/employee/{employee_id}")
async def get_employee_risk(
    stack_id: str,
    employee_id: str,
    session: AsyncSession = Depends(get_db_session),
    scorer: HumanRiskScorer = Depends(get_risk_scorer),
) -> dict:
    """Get risk score for a specific employee.

    Args:
        stack_id: Organization stack
        employee_id: Hashed employee ID
        session: DB session
        scorer: Risk scorer

    Returns:
        Employee risk profile
    """
    try:
        result = await scorer.calculate_employee_risk(session, stack_id, employee_id)
        return result
    except Exception as e:
        logger.error(f"Risk calculation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/risk/{stack_id}/organization")
async def get_organization_risk(
    stack_id: str,
    session: AsyncSession = Depends(get_db_session),
    scorer: HumanRiskScorer = Depends(get_risk_scorer),
) -> dict:
    """Get aggregate human risk for organization.

    Args:
        stack_id: Organization stack
        session: DB session
        scorer: Risk scorer

    Returns:
        Organization risk profile
    """
    try:
        result = await scorer.calculate_stack_human_risk(session, stack_id)
        return result
    except Exception as e:
        logger.error(f"Risk calculation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
