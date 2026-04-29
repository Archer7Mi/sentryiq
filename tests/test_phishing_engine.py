"""Unit tests for phishing simulation engine."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.simulation.phishing import PhishingSimulationEngine


@pytest.mark.unit
@pytest.mark.asyncio
class TestPhishingSimulationEngine:
    """Test suite for PhishingSimulationEngine."""

    @pytest.fixture
    def mock_nim(self):
        """Create mock NIM client."""
        mock = AsyncMock()
        mock.generate_phishing_email = AsyncMock(
            return_value={
                "subject": "Test Subject",
                "body": "Test email body",
                "sender_identity": "test@example.com",
            }
        )
        return mock

    @pytest.fixture
    async def engine(self, mock_nim):
        """Create PhishingSimulationEngine instance."""
        return PhishingSimulationEngine(mock_nim)

    async def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert hasattr(engine, "create_campaign")
        assert hasattr(engine, "launch_campaign")

    async def test_create_campaign(self, engine):
        """Test campaign creation."""
        campaign = await engine.create_campaign(
            stack_id="stack-123",
            campaign_type="phishing",
            target_employee_role="HR",
            company_name="Test Corp",
        )

        assert campaign is not None
        assert campaign["stack_id"] == "stack-123"
        assert campaign["campaign_type"] == "phishing"
        assert campaign["status"] == "pending"
        assert campaign["campaign_id"] is not None

    async def test_launch_campaign(self, engine):
        """Test campaign launch."""
        # Create campaign first
        campaign = await engine.create_campaign(
            stack_id="stack-123",
            campaign_type="phishing",
            target_employee_role="HR",
            company_name="Test Corp",
        )

        # Launch campaign
        result = await engine.launch_campaign(
            campaign_id=campaign["campaign_id"],
            target_employee_ids=["emp-001", "emp-002"],
        )

        assert result["success"]
        assert result["campaign_id"] == campaign["campaign_id"]
        assert result["recipients"] == 2

    async def test_record_click(self, engine):
        """Test recording employee click."""
        # Create and launch campaign
        campaign = await engine.create_campaign(
            stack_id="stack-123",
            campaign_type="phishing",
            target_employee_role="HR",
            company_name="Test Corp",
        )

        await engine.launch_campaign(
            campaign_id=campaign["campaign_id"],
            target_employee_ids=["emp-001"],
        )

        # Record click
        result = await engine.record_click(
            campaign_id=campaign["campaign_id"],
            employee_id="emp-001",
        )

        assert result["success"]
        assert result["campaign_id"] == campaign["campaign_id"]
        assert result["employee_id"] == "emp-001"

    async def test_record_report(self, engine):
        """Test recording phishing report."""
        # Create and launch campaign
        campaign = await engine.create_campaign(
            stack_id="stack-123",
            campaign_type="phishing",
            target_employee_role="HR",
            company_name="Test Corp",
        )

        await engine.launch_campaign(
            campaign_id=campaign["campaign_id"],
            target_employee_ids=["emp-001"],
        )

        # Record report
        result = await engine.record_report(
            campaign_id=campaign["campaign_id"],
            employee_id="emp-001",
        )

        assert result["success"]
        assert result["campaign_id"] == campaign["campaign_id"]

    async def test_complete_campaign(self, engine):
        """Test campaign completion."""
        # Create campaign
        campaign = await engine.create_campaign(
            stack_id="stack-123",
            campaign_type="phishing",
            target_employee_role="HR",
            company_name="Test Corp",
        )

        # Complete campaign
        result = await engine.complete_campaign(campaign["campaign_id"])

        assert result["success"]
        assert result["status"] == "completed"

    async def test_campaign_stats(self, engine):
        """Test campaign statistics."""
        # Create and launch
        campaign = await engine.create_campaign(
            stack_id="stack-123",
            campaign_type="phishing",
            target_employee_role="HR",
            company_name="Test Corp",
        )

        await engine.launch_campaign(
            campaign_id=campaign["campaign_id"],
            target_employee_ids=["emp-001", "emp-002", "emp-003"],
        )

        # Record interactions
        await engine.record_click(campaign["campaign_id"], "emp-001")
        await engine.record_click(campaign["campaign_id"], "emp-002")
        await engine.record_report(campaign["campaign_id"], "emp-003")

        # Get stats
        stats = await engine.get_campaign_stats(campaign["campaign_id"])

        assert stats["total_sent"] == 3
        assert stats["clicked"] == 2
        assert stats["reported"] == 1
        assert stats["click_rate"] == pytest.approx(66.67, abs=0.1)
        assert stats["report_rate"] == pytest.approx(33.33, abs=0.1)

    async def test_duplicate_click_handling(self, engine):
        """Test handling duplicate clicks from same employee."""
        campaign = await engine.create_campaign(
            stack_id="stack-123",
            campaign_type="phishing",
            target_employee_role="HR",
            company_name="Test Corp",
        )

        await engine.launch_campaign(
            campaign_id=campaign["campaign_id"],
            target_employee_ids=["emp-001"],
        )

        # Click once
        await engine.record_click(campaign["campaign_id"], "emp-001")

        # Click again - should not double count
        result = await engine.record_click(campaign["campaign_id"], "emp-001")

        stats = await engine.get_campaign_stats(campaign["campaign_id"])
        # Should be 1 click, not 2
        assert stats["clicked"] <= 1

    async def test_different_campaign_types(self, engine):
        """Test different campaign types."""
        campaign_types = ["phishing", "vishing", "smishing"]

        for campaign_type in campaign_types:
            campaign = await engine.create_campaign(
                stack_id="stack-123",
                campaign_type=campaign_type,
                target_employee_role="HR",
                company_name="Test Corp",
            )

            assert campaign["campaign_type"] == campaign_type
