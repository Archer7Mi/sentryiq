"""Unit tests for NemoClaw sandbox."""

import asyncio

import pytest

from backend.sandbox.monitor import SandboxMonitor
from backend.sandbox.nemoclaw import AgentCapability, SandboxLevel, SandboxPolicy


@pytest.mark.unit
@pytest.mark.asyncio
class TestNemoclawSandbox:
    """Test suite for NemoclawSandbox."""

    async def test_sandbox_initialization(self, test_sandbox):
        """Test sandbox initialization."""
        assert test_sandbox is not None
        assert test_sandbox._initialized
        assert len(test_sandbox.policies) > 0

    async def test_agent_registration(self, test_sandbox):
        """Test agent policy registration."""
        policy = SandboxPolicy(
            agent_name="test-agent",
            sandbox_level=SandboxLevel.STANDARD,
            allowed_capabilities=[AgentCapability.NIM_API_ACCESS],
            max_memory_mb=256,
        )

        result = test_sandbox.register_agent(policy)
        assert result
        assert "test-agent" in test_sandbox.policies

    async def test_agent_execution_success(self, test_sandbox):
        """Test successful agent execution."""
        policy = SandboxPolicy(
            agent_name="test-agent-success",
            sandbox_level=SandboxLevel.STANDARD,
            allowed_capabilities=[AgentCapability.JSON_PROCESSING],
            max_timeout_seconds=10,
        )
        test_sandbox.register_agent(policy)

        async def dummy_agent():
            return {"status": "ok", "value": 42}

        result = await test_sandbox.execute_agent("test-agent-success", dummy_agent)

        assert result["success"]
        assert result["result"]["status"] == "ok"
        assert result["result"]["value"] == 42
        assert "execution_id" in result
        assert result["duration_seconds"] >= 0

    async def test_agent_execution_failure(self, test_sandbox):
        """Test agent execution with error."""
        policy = SandboxPolicy(
            agent_name="test-agent-fail",
            sandbox_level=SandboxLevel.STANDARD,
            allowed_capabilities=[],
            max_timeout_seconds=10,
        )
        test_sandbox.register_agent(policy)

        async def failing_agent():
            raise ValueError("Test error")

        result = await test_sandbox.execute_agent("test-agent-fail", failing_agent)

        assert not result["success"]
        assert "error" in result
        assert "Test error" in result["error"]

    async def test_agent_timeout(self, test_sandbox):
        """Test agent timeout enforcement."""
        policy = SandboxPolicy(
            agent_name="test-agent-timeout",
            sandbox_level=SandboxLevel.STANDARD,
            allowed_capabilities=[],
            max_timeout_seconds=1,
        )
        test_sandbox.register_agent(policy)

        async def slow_agent():
            await asyncio.sleep(5)
            return "done"

        result = await test_sandbox.execute_agent("test-agent-timeout", slow_agent)

        assert not result["success"]
        assert "timeout" in result["error"].lower()

    async def test_rate_limiting(self, test_sandbox):
        """Test rate limiting enforcement."""
        policy = SandboxPolicy(
            agent_name="test-agent-rate-limit",
            sandbox_level=SandboxLevel.STANDARD,
            allowed_capabilities=[],
            max_api_calls_per_minute=1,
            max_timeout_seconds=10,
        )
        test_sandbox.register_agent(policy)

        async def dummy_agent():
            return {"ok": True}

        # First call should succeed
        result1 = await test_sandbox.execute_agent("test-agent-rate-limit", dummy_agent)
        assert result1["success"]

        # Second call should fail due to rate limit
        result2 = await test_sandbox.execute_agent("test-agent-rate-limit", dummy_agent)
        assert not result2["success"]
        assert "Rate limit" in result2["error"]

    async def test_unregistered_agent(self, test_sandbox):
        """Test execution of unregistered agent."""
        async def dummy_agent():
            return {"ok": True}

        result = await test_sandbox.execute_agent("unknown-agent", dummy_agent)

        assert not result["success"]
        assert "not registered" in result["error"]

    async def test_audit_logging(self, test_sandbox):
        """Test audit logging of executions."""
        policy = SandboxPolicy(
            agent_name="test-agent-audit",
            sandbox_level=SandboxLevel.STANDARD,
            allowed_capabilities=[],
            audit_enabled=True,
        )
        test_sandbox.register_agent(policy)

        async def dummy_agent():
            return {"ok": True}

        await test_sandbox.execute_agent("test-agent-audit", dummy_agent)

        logs = test_sandbox.get_audit_logs("test-agent-audit")
        assert len(logs) > 0
        assert logs[0]["agent_name"] == "test-agent-audit"
        assert logs[0]["success"]

    async def test_sandbox_status(self, test_sandbox):
        """Test sandbox status reporting."""
        status = test_sandbox.get_sandbox_status()

        assert status["initialized"]
        assert status["registered_agents"] > 0
        assert "agents" in status
        assert isinstance(status["agents"], list)


@pytest.mark.unit
class TestSandboxMonitor:
    """Test suite for SandboxMonitor."""

    @pytest.fixture
    def monitor(self):
        """Create SandboxMonitor instance."""
        return SandboxMonitor()

    def test_monitor_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor is not None
        assert len(monitor.agent_metrics) == 0
        assert len(monitor.anomalies) == 0

    def test_record_successful_execution(self, monitor):
        """Test recording successful execution."""
        monitor.record_execution(
            agent_name="test-agent",
            execution_id="exec-1",
            success=True,
            duration_seconds=1.5,
            memory_used_mb=256,
        )

        assert "test-agent" in monitor.agent_metrics
        assert monitor.agent_metrics["test-agent"]["total_executions"] == 1
        assert monitor.agent_metrics["test-agent"]["successful_executions"] == 1

    def test_record_failed_execution(self, monitor):
        """Test recording failed execution."""
        monitor.record_execution(
            agent_name="test-agent",
            execution_id="exec-2",
            success=False,
            duration_seconds=0.5,
            memory_used_mb=100,
            error_message="Test error",
        )

        assert monitor.agent_metrics["test-agent"]["failed_executions"] == 1
        assert monitor.agent_metrics["test-agent"]["error_count"] == 1

    def test_anomaly_detection_slow_execution(self, monitor):
        """Test anomaly detection for slow execution."""
        # Record normal execution
        monitor.record_execution(
            agent_name="test-agent",
            execution_id="exec-1",
            success=True,
            duration_seconds=1.0,
        )

        # Record slow execution (> 2.5x normal)
        monitor.record_execution(
            agent_name="test-agent",
            execution_id="exec-2",
            success=True,
            duration_seconds=3.0,
        )

        # Should detect anomaly
        assert len(monitor.anomalies) > 0

    def test_anomaly_detection_high_error_rate(self, monitor):
        """Test anomaly detection for high error rate."""
        # Record 10 failed executions
        for i in range(10):
            monitor.record_execution(
                agent_name="test-agent",
                execution_id=f"exec-{i}",
                success=False,
                duration_seconds=0.5,
                error_message="Test error",
            )

        # Record 2 successful
        for i in range(2):
            monitor.record_execution(
                agent_name="test-agent",
                execution_id=f"success-{i}",
                success=True,
                duration_seconds=1.0,
            )

        # Should detect high error rate
        assert len(monitor.anomalies) > 0

    def test_agent_health_healthy(self, monitor):
        """Test agent health status - HEALTHY."""
        for i in range(100):
            monitor.record_execution(
                agent_name="test-agent",
                execution_id=f"exec-{i}",
                success=True,
                duration_seconds=1.0,
            )

        health = monitor.get_agent_health("test-agent")
        assert health["status"] == "HEALTHY"
        assert health["success_rate"] == 1.0

    def test_agent_health_degraded(self, monitor):
        """Test agent health status - DEGRADED."""
        # 90% success rate
        for i in range(90):
            monitor.record_execution(
                agent_name="test-agent",
                execution_id=f"exec-{i}",
                success=True,
                duration_seconds=1.0,
            )

        for i in range(10):
            monitor.record_execution(
                agent_name="test-agent",
                execution_id=f"fail-{i}",
                success=False,
                duration_seconds=0.5,
            )

        health = monitor.get_agent_health("test-agent")
        assert health["status"] == "DEGRADED"
        assert 0.8 <= health["success_rate"] <= 1.0

    def test_monitoring_summary(self, monitor):
        """Test monitoring summary generation."""
        # Record various executions
        for i in range(5):
            monitor.record_execution(
                agent_name="agent1",
                execution_id=f"exec-{i}",
                success=True,
                duration_seconds=1.0,
            )

        for i in range(3):
            monitor.record_execution(
                agent_name="agent2",
                execution_id=f"exec-{i}",
                success=False,
                duration_seconds=0.5,
            )

        summary = monitor.get_summary()

        assert summary["total_executions"] == 8
        assert summary["total_successful"] == 5
        assert summary["registered_agents"] == 2
        assert "health_distribution" in summary
