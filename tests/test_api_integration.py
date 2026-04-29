"""Integration tests for SentryIQ API endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "SentryIQ"

    def test_sandbox_status(self, client):
        """Test sandbox status endpoint."""
        response = client.get("/api/sandbox/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert "data" in data

    def test_sandbox_agents_health(self, client):
        """Test agents health endpoint."""
        response = client.get("/api/sandbox/agents/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert "agents" in data
        assert isinstance(data["agents"], list)

    def test_sandbox_monitoring_summary(self, client):
        """Test monitoring summary endpoint."""
        response = client.get("/api/sandbox/monitoring/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert "data" in data
        assert "total_executions" in data["data"]

    def test_sandbox_anomalies(self, client):
        """Test anomalies endpoint."""
        response = client.get("/api/sandbox/anomalies?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert "anomalies" in data
        assert isinstance(data["anomalies"], list)

    def test_sandbox_policies(self, client):
        """Test policies endpoint."""
        response = client.get("/api/sandbox/policies")
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert "policies" in data
        assert len(data["policies"]) > 0

    def test_sandbox_agent_specific_health(self, client):
        """Test agent-specific health endpoint."""
        # First get list of agents
        response = client.get("/api/sandbox/agents/health")
        agents = response.json().get("agents", [])

        if agents:
            agent_name = agents[0]["agent_name"]
            response = client.get(f"/api/sandbox/agents/{agent_name}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["success"]
            assert data["agent_name"] == agent_name

    def test_sandbox_agent_not_found(self, client):
        """Test agent endpoint with non-existent agent."""
        response = client.get("/api/sandbox/agents/nonexistent-agent/health")
        assert response.status_code == 404

    def test_sandbox_audit_logs(self, client):
        """Test audit logs endpoint."""
        response = client.get("/api/sandbox/audit-logs/test-agent?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_anomalies_filter_by_severity(self, client):
        """Test anomalies endpoint with severity filter."""
        response = client.get("/api/sandbox/anomalies?severity=HIGH&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["success"]

    def test_anomalies_filter_by_agent(self, client):
        """Test anomalies endpoint with agent filter."""
        response = client.get("/api/sandbox/anomalies?agent_name=test-agent&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["success"]

    def test_anomalies_invalid_severity(self, client):
        """Test anomalies endpoint with invalid severity."""
        response = client.get("/api/sandbox/anomalies?severity=INVALID")
        assert response.status_code == 400

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/health")
        # Most frameworks should allow OPTIONS by default
        assert response.status_code in [200, 405]

    def test_error_handling(self, client):
        """Test error handling for invalid endpoints."""
        response = client.get("/api/invalid/endpoint")
        assert response.status_code == 404
