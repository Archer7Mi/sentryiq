"""Human risk score calculation engine.

Computes composite risk scores based on employee behavior in simulations,
CVE exposure, and compliance violations.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    EmployeeRiskScore,
    SMBStack,
    StackVulnerability,
)

logger = logging.getLogger(__name__)


class HumanRiskScorer:
    """Calculate human security risk scores."""

    def __init__(self):
        """Initialize scorer."""
        pass

    async def calculate_employee_risk(
        self,
        session: AsyncSession,
        stack_id: str,
        employee_id: str,
    ) -> dict:
        """Calculate comprehensive risk score for an employee.

        Risk = 40% (simulation behavior) + 30% (stack exposure) + 30% (compliance gap)

        Args:
            session: DB session
            stack_id: Stack UUID
            employee_id: Hashed employee identifier

        Returns:
            Risk score breakdown and recommendations
        """
        logger.info(f"Calculating risk for {employee_id} on stack {stack_id}")

        try:
            # Get employee simulation history
            emp_result = await session.execute(
                select(EmployeeRiskScore).where(
                    EmployeeRiskScore.stack_id == stack_id,
                    EmployeeRiskScore.employee_identifier == employee_id,
                )
            )
            emp_score = emp_result.scalars().first()

            if not emp_score:
                return {
                    "employee_id": employee_id,
                    "risk_score": 50.0,
                    "reason": "No simulation history",
                    "recommendations": ["Send first phishing simulation"],
                }

            # Component 1: Simulation behavior (40%)
            # Base: 50 (neutral)
            # Click penalty: +2 per click (max 15)
            # Report bonus: -1 per report (min -5)
            sim_clicks_penalty = min(15.0, emp_score.simulations_clicked * 2.0)
            sim_reports_bonus = max(-5.0, emp_score.simulations_reported * -1.0)
            sim_component = 50.0 + sim_clicks_penalty + sim_reports_bonus

            # Component 2: Stack CVE exposure (30%)
            # Count critical vulns employee could be affected by
            vuln_result = await session.execute(
                select(StackVulnerability).where(
                    StackVulnerability.stack_id == stack_id,
                    StackVulnerability.priority_label == "CRITICAL",
                )
            )
            critical_vulns = len(vuln_result.scalars().all())
            vuln_component = min(100.0, critical_vulns * 10.0)

            # Component 3: Compliance awareness (30%)
            # Get stack compliance frameworks
            stack_result = await session.execute(
                select(SMBStack).where(SMBStack.id == stack_id)
            )
            stack = stack_result.scalars().first()

            compliance_count = len(stack.compliance_frameworks) if stack else 0
            compliance_component = 50.0 + (compliance_count * 5.0)

            # Weighted average
            total_risk = (
                (sim_component * 0.40)
                + (vuln_component * 0.30)
                + (compliance_component * 0.30)
            )
            total_risk = min(100.0, max(0.0, total_risk))

            # Generate recommendations
            recommendations = self._get_recommendations(
                total_risk,
                emp_score.simulations_clicked,
                emp_score.simulations_reported,
                critical_vulns,
            )

            return {
                "employee_id": employee_id,
                "risk_score": round(total_risk, 1),
                "components": {
                    "simulation_behavior": round(sim_component, 1),
                    "cve_exposure": round(vuln_component, 1),
                    "compliance_awareness": round(compliance_component, 1),
                },
                "simulation_history": {
                    "sent": emp_score.simulations_sent,
                    "clicked": emp_score.simulations_clicked,
                    "reported": emp_score.simulations_reported,
                },
                "critical_vulnerabilities": critical_vulns,
                "risk_level": self._score_to_level(total_risk),
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Risk calculation failed: {e}")
            raise

    async def calculate_stack_human_risk(
        self,
        session: AsyncSession,
        stack_id: str,
    ) -> dict:
        """Calculate aggregate human risk for entire stack.

        Args:
            session: DB session
            stack_id: Stack UUID

        Returns:
            Stack-level risk metrics
        """
        logger.info(f"Calculating stack human risk for {stack_id}")

        try:
            # Get all employees for stack
            emp_result = await session.execute(
                select(EmployeeRiskScore).where(
                    EmployeeRiskScore.stack_id == stack_id,
                )
            )
            employees = emp_result.scalars().all()

            if not employees:
                return {
                    "stack_id": stack_id,
                    "total_employees": 0,
                    "average_risk": 50.0,
                    "high_risk_count": 0,
                    "message": "No employees tracked yet",
                }

            # Calculate individual risks
            risks = []
            for emp in employees:
                emp_risk = await self.calculate_employee_risk(
                    session,
                    stack_id,
                    emp.employee_identifier,
                )
                risks.append(emp_risk)

            avg_risk = sum(r["risk_score"] for r in risks) / len(risks)
            high_risk = sum(1 for r in risks if r["risk_score"] > 70)
            medium_risk = sum(1 for r in risks if 40 <= r["risk_score"] <= 70)
            low_risk = sum(1 for r in risks if r["risk_score"] < 40)

            return {
                "stack_id": stack_id,
                "total_employees": len(employees),
                "average_risk": round(avg_risk, 1),
                "risk_distribution": {
                    "high": high_risk,
                    "medium": medium_risk,
                    "low": low_risk,
                },
                "top_at_risk": sorted(risks, key=lambda r: r["risk_score"], reverse=True)[
                    :5
                ],
                "recommendations": self._get_stack_recommendations(
                    avg_risk, high_risk, len(employees)
                ),
            }

        except Exception as e:
            logger.error(f"Stack risk calculation failed: {e}")
            raise

    def _get_recommendations(
        self,
        risk_score: float,
        clicks: int,
        reports: int,
        critical_vulns: int,
    ) -> list[str]:
        """Generate recommendations based on risk profile.

        Args:
            risk_score: Overall risk score
            clicks: Number of simulated phishing clicks
            reports: Number of simulated emails reported
            critical_vulns: Number of critical CVEs in stack

        Returns:
            List of recommendations
        """
        recommendations = []

        if risk_score >= 80:
            recommendations.append(
                "🔴 HIGH RISK: Immediate security training required"
            )
            recommendations.append("Schedule one-on-one cybersecurity coaching")
        elif risk_score >= 60:
            recommendations.append(
                "🟠 MEDIUM-HIGH RISK: Recommend security awareness course"
            )
            recommendations.append("Include in next security briefing")
        elif risk_score >= 40:
            recommendations.append("🟡 MEDIUM RISK: Continue regular phishing simulations")
            recommendations.append("Positive progress — maintain current training")
        else:
            recommendations.append("🟢 LOW RISK: Security champion profile")
            recommendations.append("Consider for peer mentoring role")

        if clicks >= 3:
            recommendations.append(
                "⚠️ Clicks detected: Increase frequency of simulations"
            )

        if reports >= 2:
            recommendations.append(
                "✓ Good security awareness: Employee is reporting threats"
            )

        if critical_vulns > 0:
            recommendations.append(
                f"⚡ {critical_vulns} critical CVEs in infrastructure — urgent patching needed"
            )

        return recommendations

    def _get_stack_recommendations(
        self, avg_risk: float, high_risk_count: int, total_employees: int
    ) -> list[str]:
        """Generate organization-level recommendations.

        Args:
            avg_risk: Average risk score
            high_risk_count: Number of high-risk employees
            total_employees: Total employees

        Returns:
            List of recommendations
        """
        recommendations = []

        if avg_risk >= 70:
            recommendations.append("🚨 CRITICAL: Organization-wide security training urgently needed")
        elif avg_risk >= 50:
            recommendations.append("⚠️ Increase security awareness program frequency")
        else:
            recommendations.append("✓ Good overall security posture")

        high_risk_pct = (high_risk_count / total_employees * 100) if total_employees > 0 else 0
        if high_risk_pct > 30:
            recommendations.append(
                f"🔴 {high_risk_count}/{total_employees} employees at high risk — prioritize training"
            )
        elif high_risk_pct > 0:
            recommendations.append(
                f"Targeted coaching for {high_risk_count} high-risk employees"
            )

        recommendations.append("Schedule monthly phishing simulation campaigns")
        recommendations.append("Pair security awareness with patch management (both pillars)")

        return recommendations

    def _score_to_level(self, score: float) -> str:
        """Convert risk score to risk level.

        Args:
            score: Risk score 0-100

        Returns:
            Risk level: LOW, MEDIUM, HIGH, CRITICAL
        """
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
