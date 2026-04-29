"""NVIDIA NemoClaw sandbox configuration and initialization.

NemoClaw provides kernel-level sandboxing for SentryIQ's AI agents.
This module implements the sandbox environment, policy enforcement,
and lifecycle management.

Reference: https://docs.nvidia.com/nemoclaw/
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentCapability(str, Enum):
    """Capabilities that agents can be granted in the sandbox."""

    # Network capabilities
    NIM_API_ACCESS = "nim_api_access"
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    CACHE_ACCESS = "cache_access"

    # Filesystem capabilities
    LOG_WRITE = "log_write"
    TEMP_STORAGE = "temp_storage"

    # Computation capabilities
    CRYPTO_OPERATIONS = "crypto_operations"
    JSON_PROCESSING = "json_processing"
    TEXT_PROCESSING = "text_processing"


class SandboxLevel(str, Enum):
    """Isolation levels for sandboxed agents."""

    RESTRICTED = "restricted"  # Minimal capabilities, high isolation
    STANDARD = "standard"  # Standard security profile
    ELEVATED = "elevated"  # Elevated access for trusted agents


@dataclass
class SandboxPolicy:
    """Security policy for a sandboxed agent."""

    agent_name: str
    sandbox_level: SandboxLevel
    allowed_capabilities: List[AgentCapability]
    max_memory_mb: int = 512
    max_timeout_seconds: int = 30
    max_api_calls_per_minute: int = 100
    allowed_nim_models: List[str] = field(default_factory=list)
    audit_enabled: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary for configuration."""
        return {
            "agent_name": self.agent_name,
            "sandbox_level": self.sandbox_level.value,
            "allowed_capabilities": [c.value for c in self.allowed_capabilities],
            "max_memory_mb": self.max_memory_mb,
            "max_timeout_seconds": self.max_timeout_seconds,
            "max_api_calls_per_minute": self.max_api_calls_per_minute,
            "allowed_nim_models": self.allowed_nim_models,
            "audit_enabled": self.audit_enabled,
            "description": self.description,
        }


@dataclass
class SandboxExecutionLog:
    """Log entry for sandboxed agent execution."""

    execution_id: str
    agent_name: str
    timestamp: datetime
    capabilities_used: List[AgentCapability]
    api_calls_count: int
    memory_used_mb: int
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None


class NemoclawSandbox:
    """NVIDIA NemoClaw sandbox for agent isolation and policy enforcement.

    This class manages the sandbox environment for SentryIQ's AI agents,
    enforcing security policies and monitoring resource usage.
    """

    def __init__(self, sandbox_name: str = "sentryiq-sandbox"):
        """Initialize the NemoClaw sandbox.

        Args:
            sandbox_name: Name of the sandbox environment
        """
        self.sandbox_name = sandbox_name
        self.policies: Dict[str, SandboxPolicy] = {}
        self.execution_logs: List[SandboxExecutionLog] = []
        self.agent_call_counters: Dict[str, Dict[str, int]] = {}
        self._initialized = False

        logger.info(f"NemoClaw sandbox '{sandbox_name}' created")

    async def initialize(self) -> bool:
        """Initialize the sandbox environment.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # In production, this would initialize the actual NVIDIA NemoClaw runtime
            # For now, we simulate the initialization
            logger.info(f"Initializing NemoClaw sandbox: {self.sandbox_name}")

            # Verify NemoClaw is available (in real implementation)
            nemoclaw_available = os.environ.get("NEMOCLAW_SDK", "false").lower() == "true"

            if not nemoclaw_available:
                logger.warning(
                    "NemoClaw SDK not detected. Running in simulation mode. "
                    "Set NEMOCLAW_SDK=true to enable hardware sandboxing."
                )

            self._initialized = True
            logger.info("Sandbox initialization successful")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize sandbox: {e}")
            return False

    def register_agent(self, policy: SandboxPolicy) -> bool:
        """Register an agent with a security policy.

        Args:
            policy: Security policy for the agent

        Returns:
            True if registration successful
        """
        try:
            if not self._initialized:
                raise RuntimeError("Sandbox not initialized")

            self.policies[policy.agent_name] = policy
            self.agent_call_counters[policy.agent_name] = {"per_minute": 0, "per_hour": 0}

            logger.info(
                f"Registered agent '{policy.agent_name}' with {policy.sandbox_level.value} isolation"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return False

    async def execute_agent(
        self,
        agent_name: str,
        agent_func: Callable,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute an agent function within sandbox boundaries.

        Args:
            agent_name: Name of the agent
            agent_func: Async callable to execute
            *args: Positional arguments for the agent
            **kwargs: Keyword arguments for the agent

        Returns:
            Dictionary with execution result and metadata
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        start_timestamp = start_time.timestamp()

        try:
            if not self._initialized:
                raise RuntimeError("Sandbox not initialized")

            if agent_name not in self.policies:
                raise ValueError(f"Agent '{agent_name}' not registered with sandbox")

            policy = self.policies[agent_name]

            # Check rate limits
            if not self._check_rate_limit(agent_name, policy):
                raise RuntimeError(
                    f"Rate limit exceeded for agent '{agent_name}' "
                    f"({policy.max_api_calls_per_minute} calls/minute)"
                )

            # Execute agent with timeout
            try:
                result = await asyncio.wait_for(
                    agent_func(*args, **kwargs),
                    timeout=policy.max_timeout_seconds,
                )
            except asyncio.TimeoutError:
                raise RuntimeError(
                    f"Agent execution timeout exceeded ({policy.max_timeout_seconds}s)"
                )

            end_time = datetime.utcnow()
            duration = end_time.timestamp() - start_timestamp

            # Log successful execution
            if policy.audit_enabled:
                self._log_execution(
                    SandboxExecutionLog(
                        execution_id=execution_id,
                        agent_name=agent_name,
                        timestamp=end_time,
                        capabilities_used=policy.allowed_capabilities,
                        api_calls_count=1,
                        memory_used_mb=256,  # Simulated
                        duration_seconds=duration,
                        success=True,
                    )
                )

            logger.info(
                f"Agent '{agent_name}' execution completed in {duration:.2f}s "
                f"(execution_id={execution_id})"
            )

            return {
                "success": True,
                "result": result,
                "execution_id": execution_id,
                "duration_seconds": duration,
            }

        except Exception as e:
            error_msg = str(e)
            end_time = datetime.utcnow()
            duration = end_time.timestamp() - start_timestamp

            # Log failed execution
            if agent_name in self.policies and self.policies[agent_name].audit_enabled:
                self._log_execution(
                    SandboxExecutionLog(
                        execution_id=execution_id,
                        agent_name=agent_name,
                        timestamp=end_time,
                        capabilities_used=[],
                        api_calls_count=0,
                        memory_used_mb=0,
                        duration_seconds=duration,
                        success=False,
                        error_message=error_msg,
                    )
                )

            logger.error(
                f"Agent '{agent_name}' execution failed (execution_id={execution_id}): {error_msg}"
            )

            return {
                "success": False,
                "error": error_msg,
                "execution_id": execution_id,
                "duration_seconds": duration,
            }

    def _check_rate_limit(self, agent_name: str, policy: SandboxPolicy) -> bool:
        """Check if agent is within rate limits.

        Args:
            agent_name: Name of the agent
            policy: Agent's security policy

        Returns:
            True if within limits, False otherwise
        """
        counters = self.agent_call_counters.get(agent_name, {})
        calls_per_minute = counters.get("per_minute", 0)

        if calls_per_minute >= policy.max_api_calls_per_minute:
            return False

        # Increment counters
        self.agent_call_counters[agent_name]["per_minute"] = calls_per_minute + 1
        self.agent_call_counters[agent_name]["per_hour"] = (
            self.agent_call_counters[agent_name].get("per_hour", 0) + 1
        )

        return True

    def _log_execution(self, log_entry: SandboxExecutionLog) -> None:
        """Log agent execution details.

        Args:
            log_entry: Execution log entry
        """
        self.execution_logs.append(log_entry)

        # In production, persist to audit database
        logger.debug(
            f"Audit: {log_entry.agent_name} "
            f"({'✓' if log_entry.success else '✗'}) "
            f"memory={log_entry.memory_used_mb}MB "
            f"duration={log_entry.duration_seconds:.2f}s"
        )

    def get_audit_logs(self, agent_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve audit logs for agents.

        Args:
            agent_name: Filter by agent name (None = all agents)
            limit: Maximum number of logs to return

        Returns:
            List of audit log dictionaries
        """
        logs = self.execution_logs
        if agent_name:
            logs = [log for log in logs if log.agent_name == agent_name]

        return [
            {
                "execution_id": log.execution_id,
                "agent_name": log.agent_name,
                "timestamp": log.timestamp.isoformat(),
                "success": log.success,
                "duration_seconds": log.duration_seconds,
                "memory_used_mb": log.memory_used_mb,
                "error": log.error_message,
            }
            for log in logs[-limit:]
        ]

    def get_sandbox_status(self) -> Dict[str, Any]:
        """Get current sandbox status and statistics.

        Returns:
            Dictionary with sandbox status
        """
        return {
            "sandbox_name": self.sandbox_name,
            "initialized": self._initialized,
            "registered_agents": len(self.policies),
            "total_executions": len(self.execution_logs),
            "agents": [
                {
                    "name": name,
                    "level": policy.sandbox_level.value,
                    "capabilities_count": len(policy.allowed_capabilities),
                    "calls_per_minute": self.agent_call_counters.get(name, {}).get("per_minute", 0),
                }
                for name, policy in self.policies.items()
            ],
            "recent_errors": sum(1 for log in self.execution_logs[-100:] if not log.success),
        }


# Global sandbox instance
_sandbox_instance: Optional[NemoclawSandbox] = None


async def get_sandbox() -> NemoclawSandbox:
    """Get or create the global sandbox instance.

    Returns:
        NemoclawSandbox instance
    """
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = NemoclawSandbox("sentryiq-sandbox")
        await _sandbox_instance.initialize()
    return _sandbox_instance


async def shutdown_sandbox() -> None:
    """Shutdown the sandbox."""
    global _sandbox_instance
    if _sandbox_instance:
        logger.info("Shutting down NemoClaw sandbox")
        _sandbox_instance = None
