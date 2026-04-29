"""Unit tests for human risk scoring engine."""

import pytest

from backend.simulation.scoring import HumanRiskScorer


@pytest.mark.unit
class TestHumanRiskScorer:
    """Test suite for HumanRiskScorer."""

    @pytest.fixture
    def scorer(self):
        """Create HumanRiskScorer instance."""
        return HumanRiskScorer()

    def test_initialization(self, scorer):
        """Test HumanRiskScorer initialization."""
        assert scorer is not None
        assert hasattr(scorer, "calculate_employee_risk")
        assert hasattr(scorer, "calculate_stack_human_risk")

    def test_low_risk_employee(self, scorer):
        """Test LOW risk employee."""
        risk_score, risk_level, _ = scorer.calculate_employee_risk(
            clicks=0,
            reports=5,
            critical_vuln_count=0,
            compliance_frameworks_count=2,
        )

        assert risk_level == "LOW"
        assert risk_score < 40

    def test_medium_risk_employee(self, scorer):
        """Test MEDIUM risk employee."""
        risk_score, risk_level, _ = scorer.calculate_employee_risk(
            clicks=3,
            reports=1,
            critical_vuln_count=1,
            compliance_frameworks_count=1,
        )

        assert risk_level == "MEDIUM"
        assert 40 <= risk_score < 60

    def test_high_risk_employee(self, scorer):
        """Test HIGH risk employee."""
        risk_score, risk_level, _ = scorer.calculate_employee_risk(
            clicks=8,
            reports=0,
            critical_vuln_count=3,
            compliance_frameworks_count=0,
        )

        assert risk_level == "HIGH"
        assert 60 <= risk_score < 80

    def test_critical_risk_employee(self, scorer):
        """Test CRITICAL risk employee."""
        risk_score, risk_level, _ = scorer.calculate_employee_risk(
            clicks=10,
            reports=0,
            critical_vuln_count=5,
            compliance_frameworks_count=0,
        )

        assert risk_level == "CRITICAL"
        assert risk_score >= 80

    def test_simulation_component_calculation(self, scorer):
        """Test simulation behavior component (40%)."""
        # Base 50 + 2 per click (max +15) - 1 per report (min -5)
        # With 5 clicks: 50 + 10 = 60
        risk_score, _, _ = scorer.calculate_employee_risk(
            clicks=5,
            reports=0,
            critical_vuln_count=0,
            compliance_frameworks_count=0,
        )

        # Should be influenced by simulation component
        assert risk_score > 0

    def test_report_reduces_risk(self, scorer):
        """Test that reports reduce risk score."""
        score_with_click = scorer.calculate_employee_risk(
            clicks=5,
            reports=0,
            critical_vuln_count=0,
            compliance_frameworks_count=0,
        )[0]

        score_with_click_and_report = scorer.calculate_employee_risk(
            clicks=5,
            reports=1,
            critical_vuln_count=0,
            compliance_frameworks_count=0,
        )[0]

        # Report should reduce score
        assert score_with_click_and_report < score_with_click

    def test_cve_exposure_component(self, scorer):
        """Test CVE exposure component (30%)."""
        # Critical vuln count × 10 (capped at 100)
        score_no_vuln, _, _ = scorer.calculate_employee_risk(
            clicks=0,
            reports=0,
            critical_vuln_count=0,
            compliance_frameworks_count=0,
        )

        score_with_vulns, _, _ = scorer.calculate_employee_risk(
            clicks=0,
            reports=0,
            critical_vuln_count=5,
            compliance_frameworks_count=0,
        )

        # More vulns should increase risk
        assert score_with_vulns > score_no_vuln

    def test_compliance_component(self, scorer):
        """Test compliance awareness component (30%)."""
        # Base 50 + framework_count × 5
        score_low_compliance, _, _ = scorer.calculate_employee_risk(
            clicks=0,
            reports=0,
            critical_vuln_count=0,
            compliance_frameworks_count=1,
        )

        score_high_compliance, _, _ = scorer.calculate_employee_risk(
            clicks=0,
            reports=0,
            critical_vuln_count=0,
            compliance_frameworks_count=5,
        )

        # More compliance frameworks should reduce risk
        assert score_high_compliance <= score_low_compliance

    def test_score_range(self, scorer):
        """Test that risk scores are in 0-100 range."""
        test_cases = [
            (0, 0, 0, 0),      # Minimum
            (0, 10, 0, 0),     # Max reports
            (10, 0, 10, 10),   # High clicks & vulns
            (5, 3, 5, 5),      # Mid values
        ]

        for clicks, reports, vulns, frameworks in test_cases:
            score, _, _ = scorer.calculate_employee_risk(
                clicks=clicks,
                reports=reports,
                critical_vuln_count=vulns,
                compliance_frameworks_count=frameworks,
            )
            assert 0 <= score <= 100

    def test_recommendations_provided(self, scorer):
        """Test that recommendations are provided."""
        _, _, recommendations = scorer.calculate_employee_risk(
            clicks=5,
            reports=0,
            critical_vuln_count=2,
            compliance_frameworks_count=1,
        )

        assert recommendations is not None
        assert len(recommendations) > 0
        assert isinstance(recommendations, list)
        assert all(isinstance(r, str) for r in recommendations)

    def test_consistent_scoring(self, scorer):
        """Test that scoring is consistent."""
        params = {
            "clicks": 3,
            "reports": 1,
            "critical_vuln_count": 2,
            "compliance_frameworks_count": 2,
        }

        score1, level1, _ = scorer.calculate_employee_risk(**params)
        score2, level2, _ = scorer.calculate_employee_risk(**params)

        assert score1 == score2
        assert level1 == level2
