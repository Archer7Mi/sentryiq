"""Sandbox monitoring and audit trail management.

Tracks sandboxed agent execution, detects anomalies, and provides
security insights for the SentryIQ platform.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SandboxMonitor:
    """Monitor and analyze sandboxed agent execution patterns."""

    def __init__(self, retention_days: int = 30):
        """Initialize sandbox monitor.

        Args:
            retention_days: Days to retain audit logs
        """
        self.retention_days = retention_days
        self.anomalies: List[Dict[str, Any]] = []
        self.agent_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_duration_seconds": 0,
                "total_memory_used_mb": 0,
                "average_duration_seconds": 0,
                "error_count": 0,
            }
        )

    def record_execution(
        self,
        agent_name: str,
        execution_id: str,
        success: bool,
        duration_seconds: float,
        memory_used_mb: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Record an agent execution for monitoring.

        Args:
            agent_name: Name of the agent
            execution_id: Unique execution ID
            success: Whether execution succeeded
            duration_seconds: Execution duration in seconds
            memory_used_mb: Memory used in MB
            error_message: Error message if failed
        """
        metrics = self.agent_metrics[agent_name]
        metrics["total_executions"] += 1

        if success:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1
            metrics["error_count"] += 1

        metrics["total_duration_seconds"] += duration_seconds
        metrics["total_memory_used_mb"] += memory_used_mb

        if metrics["total_executions"] > 0:
            metrics["average_duration_seconds"] = (
                metrics["total_duration_seconds"] / metrics["total_executions"]
            )

        # Detect anomalies
        self._check_for_anomalies(agent_name, duration_seconds, memory_used_mb, error_message)

    def _check_for_anomalies(
        self,
        agent_name: str,
        duration_seconds: float,
        memory_used_mb: int,
        error_message: Optional[str],
    ) -> None:
        """Check for execution anomalies.

        Args:
            agent_name: Name of the agent
            duration_seconds: Execution duration
            memory_used_mb: Memory used
            error_message: Error message if any
        """
        metrics = self.agent_metrics[agent_name]
        anomaly_detected = False
        reasons: List[str] = []

        # Check for slow execution
        if metrics["average_duration_seconds"] > 0:
            avg_duration = metrics["average_duration_seconds"]
            if duration_seconds > avg_duration * 2.5:
                anomaly_detected = True
                reasons.append(
                    f"Slow execution: {duration_seconds:.2f}s "
                    f"(avg: {avg_duration:.2f}s)"
                )

        # Check for high error rate
        if metrics["total_executions"] >= 10:
            error_rate = metrics["error_count"] / metrics["total_executions"]
            if error_rate > 0.2:
                anomaly_detected = True
                reasons.append(f"High error rate: {error_rate:.1%}")

        # Check for repeated errors
        if error_message:
            anomaly_detected = True
            reasons.append(f"Execution error: {error_message}")

        if anomaly_detected:
            anomaly = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": agent_name,
                "duration_seconds": duration_seconds,
                "memory_used_mb": memory_used_mb,
                "reasons": reasons,
                "severity": self._calculate_severity(reasons),
            }
            self.anomalies.append(anomaly)
            logger.warning(f"Anomaly detected for {agent_name}: {', '.join(reasons)}")

    def _calculate_severity(self, reasons: List[str]) -> str:
        """Calculate anomaly severity.

        Args:
            reasons: List of anomaly reasons

        Returns:
            Severity level: LOW, MEDIUM, HIGH
        """
        if any("High error rate" in r for r in reasons):
            return "HIGH"
        if any("repeated" in r.lower() for r in reasons):
            return "MEDIUM"
        return "LOW"

    def get_agent_health(self, agent_name: str) -> Dict[str, Any]:
        """Get health status for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with health metrics
        """
        metrics = self.agent_metrics.get(agent_name, {})

        if not metrics or metrics["total_executions"] == 0:
            return {
                "agent_name": agent_name,
                "status": "NO_DATA",
                "total_executions": 0,
                "success_rate": 0.0,
            }

        success_rate = (
            metrics["successful_executions"] / metrics["total_executions"]
            if metrics["total_executions"] > 0
            else 0.0
        )

        # Determine health status
        if success_rate >= 0.95:
            status = "HEALTHY"
        elif success_rate >= 0.80:
            status = "DEGRADED"
        else:
            status = "UNHEALTHY"

        return {
            "agent_name": agent_name,
            "status": status,
            "total_executions": metrics["total_executions"],
            "successful_executions": metrics["successful_executions"],
            "failed_executions": metrics["failed_executions"],
            "success_rate": success_rate,
            "average_duration_seconds": metrics["average_duration_seconds"],
            "total_memory_used_mb": metrics["total_memory_used_mb"],
            "error_count": metrics["error_count"],
        }

    def get_all_agents_health(self) -> List[Dict[str, Any]]:
        """Get health status for all agents.

        Returns:
            List of agent health dictionaries
        """
        return [self.get_agent_health(agent_name) for agent_name in self.agent_metrics.keys()]

    def get_anomalies(
        self, agent_name: Optional[str] = None, severity: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recorded anomalies.

        Args:
            agent_name: Filter by agent name
            severity: Filter by severity (LOW, MEDIUM, HIGH)
            limit: Maximum number of anomalies to return

        Returns:
            List of anomaly records
        """
        anomalies = self.anomalies

        if agent_name:
            anomalies = [a for a in anomalies if a["agent_name"] == agent_name]

        if severity:
            anomalies = [a for a in anomalies if a["severity"] == severity]

        return anomalies[-limit:]

    def get_summary(self) -> Dict[str, Any]:
        """Get sandbox monitoring summary.

        Returns:
            Summary dictionary
        """
        total_executions = sum(m["total_executions"] for m in self.agent_metrics.values())
        total_successful = sum(
            m["successful_executions"] for m in self.agent_metrics.values()
        )

        overall_success_rate = (
            total_successful / total_executions if total_executions > 0 else 0.0
        )

        # Calculate health distribution
        all_health = self.get_all_agents_health()
        health_distribution = {
            "HEALTHY": sum(1 for h in all_health if h["status"] == "HEALTHY"),
            "DEGRADED": sum(1 for h in all_health if h["status"] == "DEGRADED"),
            "UNHEALTHY": sum(1 for h in all_health if h["status"] == "UNHEALTHY"),
            "NO_DATA": sum(1 for h in all_health if h["status"] == "NO_DATA"),
        }

        # Get high severity anomalies
        high_severity = [a for a in self.anomalies if a["severity"] == "HIGH"]

        return {
            "total_executions": total_executions,
            "total_successful": total_successful,
            "overall_success_rate": overall_success_rate,
            "registered_agents": len(self.agent_metrics),
            "health_distribution": health_distribution,
            "total_anomalies": len(self.anomalies),
            "high_severity_anomalies": len(high_severity),
            "recent_anomalies": self.anomalies[-5:] if self.anomalies else [],
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global monitor instance
_monitor_instance: Optional[SandboxMonitor] = None


def get_monitor() -> SandboxMonitor:
    """Get or create the global monitor instance.

    Returns:
        SandboxMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SandboxMonitor()
    return _monitor_instance
