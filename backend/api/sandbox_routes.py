"""Sandbox monitoring and audit API endpoints.

Exposes sandbox status, monitoring data, and audit logs
through FastAPI endpoints. These are used for security dashboards
and compliance reporting.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.sandbox.monitor import get_monitor
from backend.sandbox.nemoclaw import get_sandbox

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])


@router.get("/status")
async def get_sandbox_status():
    """Get current sandbox status and statistics.

    Returns:
        Sandbox status dictionary
    """
    try:
        sandbox = await get_sandbox()
        status = sandbox.get_sandbox_status()
        return {
            "success": True,
            "data": status,
        }
    except Exception as e:
        logger.error(f"Failed to get sandbox status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sandbox status")


@router.get("/agents/health")
async def get_agents_health():
    """Get health status for all sandboxed agents.

    Returns:
        List of agent health metrics
    """
    try:
        monitor = get_monitor()
        health = monitor.get_all_agents_health()
        return {
            "success": True,
            "agents": health,
            "timestamp": monitor.agent_metrics,
        }
    except Exception as e:
        logger.error(f"Failed to get agents health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent health")


@router.get("/agents/{agent_name}/health")
async def get_agent_health(agent_name: str):
    """Get health status for a specific agent.

    Args:
        agent_name: Name of the agent

    Returns:
        Agent health metrics
    """
    try:
        monitor = get_monitor()
        health = monitor.get_agent_health(agent_name)

        if health["status"] == "NO_DATA":
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        return {
            "success": True,
            "agent_name": agent_name,
            "health": health,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health for agent '{agent_name}': {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent health")


@router.get("/monitoring/summary")
async def get_monitoring_summary():
    """Get overall sandbox monitoring summary.

    Returns:
        Monitoring summary with statistics and anomalies
    """
    try:
        monitor = get_monitor()
        summary = monitor.get_summary()
        return {
            "success": True,
            "data": summary,
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve monitoring summary")


@router.get("/anomalies")
async def get_anomalies(
    agent_name: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
):
    """Get recorded anomalies.

    Args:
        agent_name: Filter by agent name
        severity: Filter by severity (LOW, MEDIUM, HIGH)
        limit: Maximum number of anomalies to return

    Returns:
        List of anomalies
    """
    try:
        # Validate severity parameter
        if severity and severity not in ["LOW", "MEDIUM", "HIGH"]:
            raise HTTPException(
                status_code=400,
                detail="Severity must be one of: LOW, MEDIUM, HIGH",
            )

        monitor = get_monitor()
        anomalies = monitor.get_anomalies(
            agent_name=agent_name,
            severity=severity,
            limit=limit,
        )

        return {
            "success": True,
            "anomalies": anomalies,
            "count": len(anomalies),
            "filters": {
                "agent_name": agent_name,
                "severity": severity,
                "limit": limit,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get anomalies: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve anomalies")


@router.get("/audit-logs/{agent_name}")
async def get_audit_logs(
    agent_name: str,
    limit: int = 100,
):
    """Get audit logs for a specific agent.

    Args:
        agent_name: Name of the agent
        limit: Maximum number of logs to return

    Returns:
        List of audit log entries
    """
    try:
        sandbox = await get_sandbox()
        logs = sandbox.get_audit_logs(agent_name=agent_name, limit=limit)

        if not logs:
            return {
                "success": True,
                "agent_name": agent_name,
                "logs": [],
                "message": f"No audit logs found for agent '{agent_name}'",
            }

        return {
            "success": True,
            "agent_name": agent_name,
            "logs": logs,
            "count": len(logs),
        }
    except Exception as e:
        logger.error(f"Failed to get audit logs for '{agent_name}': {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


@router.get("/policies")
async def get_policies():
    """Get all registered sandbox policies.

    Returns:
        List of sandbox policies
    """
    try:
        sandbox = await get_sandbox()
        policies = [policy.to_dict() for policy in sandbox.policies.values()]
        return {
            "success": True,
            "policies": policies,
            "count": len(policies),
        }
    except Exception as e:
        logger.error(f"Failed to get policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve policies")


@router.post("/agents/{agent_name}/restart")
async def restart_agent(agent_name: str):
    """Restart a sandboxed agent (reset rate limits).

    Args:
        agent_name: Name of the agent to restart

    Returns:
        Restart confirmation
    """
    try:
        sandbox = await get_sandbox()

        if agent_name not in sandbox.policies:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        # Reset rate counters for the agent
        sandbox.agent_call_counters[agent_name] = {"per_minute": 0, "per_hour": 0}

        logger.info(f"Rate limits reset for agent '{agent_name}'")

        return {
            "success": True,
            "message": f"Agent '{agent_name}' rate limits reset",
            "agent_name": agent_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart agent '{agent_name}': {e}")
        raise HTTPException(status_code=500, detail="Failed to restart agent")
