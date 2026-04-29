"""Phishing simulation campaign engine.

Generates realistic phishing emails and tracks employee interactions
for human risk scoring.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ai.nim_client import NIMClient
from database.models import (
    EmployeeRiskScore,
    SimulationCampaign,
    SMBStack,
)

logger = logging.getLogger(__name__)


class PhishingSimulationEngine:
    """Generate and manage phishing simulation campaigns."""

    def __init__(self, nim_client: NIMClient):
        """Initialize engine with NIM client.

        Args:
            nim_client: NVIDIA NIM client for email generation
        """
        self.nim_client = nim_client

    async def create_campaign(
        self,
        session: AsyncSession,
        stack_id: str,
        campaign_type: str,
        target_employee_role: str,
        company_name: str,
    ) -> dict:
        """Create a phishing simulation campaign.

        Args:
            session: DB session
            stack_id: Target stack UUID
            campaign_type: 'phishing', 'vishing', 'smishing'
            target_employee_role: e.g., 'HR', 'Finance', 'IT'
            company_name: Organization name for context

        Returns:
            Campaign summary with id, email_content, status
        """
        logger.info(f"Creating campaign for stack {stack_id}, role {target_employee_role}")

        try:
            # Verify stack exists
            result = await session.execute(
                select(SMBStack).where(SMBStack.id == stack_id)
            )
            stack = result.scalars().first()

            if not stack:
                raise ValueError(f"Stack not found: {stack_id}")

            # Generate phishing email via NIM
            nim_response = await self.nim_client.generate_phishing_email(
                target_role=target_employee_role,
                company_context=company_name,
            )

            # Create campaign record
            campaign = SimulationCampaign(
                id=str(uuid.uuid4()),
                stack_id=stack_id,
                campaign_type=campaign_type,
                target_employee_role=target_employee_role,
                email_content=nim_response.get("body", ""),
                status="pending",
                launched_at=None,
                completed_at=None,
            )

            session.add(campaign)
            await session.commit()

            return {
                "campaign_id": campaign.id,
                "stack_id": stack_id,
                "campaign_type": campaign_type,
                "target_role": target_employee_role,
                "email_subject": nim_response.get("subject", ""),
                "email_body": nim_response.get("body", "")[:200] + "...",
                "sender_identity": nim_response.get("sender_identity", ""),
                "status": "pending",
                "message": "Campaign created. Ready to launch.",
            }

        except Exception as e:
            logger.error(f"Campaign creation failed: {e}")
            raise

    async def launch_campaign(
        self,
        session: AsyncSession,
        campaign_id: str,
        target_employee_ids: list[str],
    ) -> dict:
        """Launch a campaign to target employees.

        Args:
            session: DB session
            campaign_id: Campaign UUID
            target_employee_ids: List of employee identifiers (hashed)

        Returns:
            Launch summary with sent count
        """
        logger.info(
            f"Launching campaign {campaign_id} to {len(target_employee_ids)} employees"
        )

        try:
            # Fetch campaign
            result = await session.execute(
                select(SimulationCampaign).where(SimulationCampaign.id == campaign_id)
            )
            campaign = result.scalars().first()

            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            if campaign.status != "pending":
                raise ValueError(f"Campaign not in pending state: {campaign.status}")

            # Update campaign status
            campaign.status = "sent"
            campaign.launched_at = datetime.utcnow()

            # Initialize or fetch employee risk scores
            for emp_id in target_employee_ids:
                emp_result = await session.execute(
                    select(EmployeeRiskScore).where(
                        EmployeeRiskScore.stack_id == campaign.stack_id,
                        EmployeeRiskScore.employee_identifier == emp_id,
                    )
                )
                emp_score = emp_result.scalars().first()

                if not emp_score:
                    emp_score = EmployeeRiskScore(
                        id=str(uuid.uuid4()),
                        stack_id=campaign.stack_id,
                        employee_identifier=emp_id,
                        risk_score=50.0,
                        simulations_sent=0,
                        simulations_clicked=0,
                        simulations_reported=0,
                        last_updated=datetime.utcnow(),
                    )
                    session.add(emp_score)
                else:
                    emp_score.simulations_sent += 1
                    emp_score.last_updated = datetime.utcnow()

            await session.commit()

            return {
                "campaign_id": campaign_id,
                "status": "sent",
                "employees_targeted": len(target_employee_ids),
                "launched_at": campaign.launched_at.isoformat(),
                "message": f"Campaign launched to {len(target_employee_ids)} employees",
            }

        except Exception as e:
            logger.error(f"Campaign launch failed: {e}")
            raise

    async def record_click(
        self,
        session: AsyncSession,
        campaign_id: str,
        employee_id: str,
    ) -> dict:
        """Record that an employee clicked the phishing link.

        Args:
            session: DB session
            campaign_id: Campaign UUID
            employee_id: Hashed employee identifier

        Returns:
            Updated risk score
        """
        logger.info(f"Recording click: campaign {campaign_id}, employee {employee_id}")

        try:
            # Update campaign
            result = await session.execute(
                select(SimulationCampaign).where(SimulationCampaign.id == campaign_id)
            )
            campaign = result.scalars().first()

            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            # Update employee risk score
            emp_result = await session.execute(
                select(EmployeeRiskScore).where(
                    EmployeeRiskScore.stack_id == campaign.stack_id,
                    EmployeeRiskScore.employee_identifier == employee_id,
                )
            )
            emp_score = emp_result.scalars().first()

            if emp_score:
                emp_score.simulations_clicked += 1
                emp_score.risk_score = min(100.0, emp_score.risk_score + 5.0)
                emp_score.last_updated = datetime.utcnow()
                await session.commit()

                return {
                    "employee_id": employee_id,
                    "risk_score": float(emp_score.risk_score),
                    "times_clicked": emp_score.simulations_clicked,
                    "message": "Click recorded. Risk score increased.",
                }

            return {"message": "Employee not found"}

        except Exception as e:
            logger.error(f"Click recording failed: {e}")
            raise

    async def record_report(
        self,
        session: AsyncSession,
        campaign_id: str,
        employee_id: str,
    ) -> dict:
        """Record that an employee reported the phishing email.

        Args:
            session: DB session
            campaign_id: Campaign UUID
            employee_id: Hashed employee identifier

        Returns:
            Updated risk score
        """
        logger.info(f"Recording report: campaign {campaign_id}, employee {employee_id}")

        try:
            # Update employee risk score
            emp_result = await session.execute(
                select(EmployeeRiskScore).where(
                    EmployeeRiskScore.employee_identifier == employee_id,
                )
            )
            emp_score = emp_result.scalars().first()

            if emp_score:
                emp_score.simulations_reported += 1
                emp_score.risk_score = max(0.0, emp_score.risk_score - 10.0)
                emp_score.last_updated = datetime.utcnow()
                await session.commit()

                return {
                    "employee_id": employee_id,
                    "risk_score": float(emp_score.risk_score),
                    "times_reported": emp_score.simulations_reported,
                    "message": "Report recorded. Risk score decreased (good behavior).",
                }

            return {"message": "Employee not found"}

        except Exception as e:
            logger.error(f"Report recording failed: {e}")
            raise

    async def complete_campaign(
        self,
        session: AsyncSession,
        campaign_id: str,
    ) -> dict:
        """Mark a campaign as completed.

        Args:
            session: DB session
            campaign_id: Campaign UUID

        Returns:
            Campaign summary
        """
        logger.info(f"Completing campaign {campaign_id}")

        try:
            result = await session.execute(
                select(SimulationCampaign).where(SimulationCampaign.id == campaign_id)
            )
            campaign = result.scalars().first()

            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            campaign.status = "completed"
            campaign.completed_at = datetime.utcnow()

            await session.commit()

            return {
                "campaign_id": campaign_id,
                "status": "completed",
                "completed_at": campaign.completed_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Campaign completion failed: {e}")
            raise

    async def get_campaign_stats(
        self,
        session: AsyncSession,
        campaign_id: str,
    ) -> dict:
        """Get statistics for a campaign.

        Args:
            session: DB session
            campaign_id: Campaign UUID

        Returns:
            Campaign stats (sent, clicked, reported)
        """
        try:
            result = await session.execute(
                select(SimulationCampaign).where(SimulationCampaign.id == campaign_id)
            )
            campaign = result.scalars().first()

            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            # Count employee interactions
            emp_result = await session.execute(
                select(EmployeeRiskScore).where(
                    EmployeeRiskScore.stack_id == campaign.stack_id,
                )
            )
            employees = emp_result.scalars().all()

            total_sent = sum(e.simulations_sent for e in employees)
            total_clicked = sum(e.simulations_clicked for e in employees)
            total_reported = sum(e.simulations_reported for e in employees)

            click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
            report_rate = (total_reported / total_sent * 100) if total_sent > 0 else 0

            return {
                "campaign_id": campaign_id,
                "campaign_type": campaign.campaign_type,
                "status": campaign.status,
                "total_employees": len(employees),
                "total_sent": total_sent,
                "total_clicked": total_clicked,
                "click_rate_percent": round(click_rate, 1),
                "total_reported": total_reported,
                "report_rate_percent": round(report_rate, 1),
                "launched_at": campaign.launched_at.isoformat() if campaign.launched_at else None,
                "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
            }

        except Exception as e:
            logger.error(f"Stats retrieval failed: {e}")
            raise
