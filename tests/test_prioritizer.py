"""Unit tests for vulnerability prioritization engine."""

import pytest

from backend.intelligence.prioritizer import Prioritizer


@pytest.mark.unit
class TestPrioritizer:
    """Test suite for Prioritizer."""

    @pytest.fixture
    def prioritizer(self):
        """Create Prioritizer instance."""
        return Prioritizer()

    def test_initialization(self, prioritizer):
        """Test Prioritizer initialization."""
        assert prioritizer is not None
        assert hasattr(prioritizer, "calculate_priority")

    def test_critical_priority_assignment(self, prioritizer):
        """Test CRITICAL priority assignment."""
        priority_score, priority_label = prioritizer.calculate_priority(
            cvss_score=9.5,
            epss_score=0.95,
            is_kev=True,
            chain_score=80.0,
        )

        assert priority_label == "CRITICAL"
        assert priority_score >= 85

    def test_high_priority_assignment(self, prioritizer):
        """Test HIGH priority assignment."""
        priority_score, priority_label = prioritizer.calculate_priority(
            cvss_score=8.0,
            epss_score=0.70,
            is_kev=False,
            chain_score=50.0,
        )

        assert priority_label == "HIGH"
        assert 70 <= priority_score < 85

    def test_medium_priority_assignment(self, prioritizer):
        """Test MEDIUM priority assignment."""
        priority_score, priority_label = prioritizer.calculate_priority(
            cvss_score=6.0,
            epss_score=0.40,
            is_kev=False,
            chain_score=30.0,
        )

        assert priority_label == "MEDIUM"
        assert 50 <= priority_score < 70

    def test_low_priority_assignment(self, prioritizer):
        """Test LOW priority assignment."""
        priority_score, priority_label = prioritizer.calculate_priority(
            cvss_score=3.0,
            epss_score=0.10,
            is_kev=False,
            chain_score=0.0,
        )

        assert priority_label == "LOW"
        assert priority_score < 50

    def test_kev_bonus(self, prioritizer):
        """Test KEV bonus application."""
        score_with_kev, _ = prioritizer.calculate_priority(
            cvss_score=7.0,
            epss_score=0.50,
            is_kev=True,
            chain_score=0.0,
        )

        score_without_kev, _ = prioritizer.calculate_priority(
            cvss_score=7.0,
            epss_score=0.50,
            is_kev=False,
            chain_score=0.0,
        )

        # KEV should boost score
        assert score_with_kev > score_without_kev

    def test_chain_bonus(self, prioritizer):
        """Test chain score bonus."""
        score_with_chain, _ = prioritizer.calculate_priority(
            cvss_score=7.0,
            epss_score=0.50,
            is_kev=False,
            chain_score=60.0,
        )

        score_without_chain, _ = prioritizer.calculate_priority(
            cvss_score=7.0,
            epss_score=0.50,
            is_kev=False,
            chain_score=0.0,
        )

        # Chain should boost score
        assert score_with_chain > score_without_chain

    def test_score_range(self, prioritizer):
        """Test that priority scores are in 0-100 range."""
        test_cases = [
            (10.0, 1.0, True, 100.0),  # Max scores
            (0.0, 0.0, False, 0.0),    # Min scores
            (5.0, 0.5, True, 50.0),    # Mid scores
        ]

        for cvss, epss, kev, chain in test_cases:
            score, _ = prioritizer.calculate_priority(
                cvss_score=min(10.0, cvss),
                epss_score=min(1.0, epss),
                is_kev=kev,
                chain_score=chain,
            )
            assert 0 <= score <= 100

    def test_consistent_scoring(self, prioritizer):
        """Test that scoring is consistent."""
        params = {
            "cvss_score": 7.5,
            "epss_score": 0.65,
            "is_kev": True,
            "chain_score": 45.0,
        }

        score1, label1 = prioritizer.calculate_priority(**params)
        score2, label2 = prioritizer.calculate_priority(**params)

        assert score1 == score2
        assert label1 == label2
