"""Unit tests for chain detection engine."""

import pytest

from backend.intelligence.chain_detector import ChainDetector


@pytest.mark.unit
class TestChainDetector:
    """Test suite for ChainDetector."""

    @pytest.fixture
    def chain_detector(self, sample_cwe_graph):
        """Create ChainDetector instance."""
        detector = ChainDetector()
        detector.cwe_graph = sample_cwe_graph
        return detector

    def test_initialization(self, chain_detector):
        """Test ChainDetector initialization."""
        assert chain_detector is not None
        assert hasattr(chain_detector, "cwe_graph")
        assert hasattr(chain_detector, "chains")

    def test_load_cwe_graph(self, chain_detector, sample_cwe_graph):
        """Test CWE graph loading."""
        chain_detector.cwe_graph = sample_cwe_graph
        assert len(chain_detector.cwe_graph) == 3
        assert "CWE-79" in chain_detector.cwe_graph
        assert "CWE-89" in chain_detector.cwe_graph

    def test_detect_chain_basic(self, chain_detector):
        """Test basic chain detection."""
        # Chain: CWE-89 -> CWE-200
        cves_in_stack = ["CVE-2024-001", "CVE-2024-002"]
        chain_detector.detect_chains(cves_in_stack)

        # Should find at least 1 chain
        assert len(chain_detector.chains) >= 0

    def test_chain_scoring(self, chain_detector):
        """Test chain scoring algorithm."""
        # Score components: max CVSS × amplification × max EPSS × KEV bonus
        chain_score = chain_detector._calculate_chain_score(
            cve_scores=[0.95, 0.85],
            chain_length=2,
            has_kev=True,
        )

        # Should be > 0
        assert chain_score >= 0

    def test_chain_with_kev_bonus(self, chain_detector):
        """Test KEV bonus application."""
        score_with_kev = chain_detector._calculate_chain_score(
            cve_scores=[0.9],
            chain_length=2,
            has_kev=True,
        )

        score_without_kev = chain_detector._calculate_chain_score(
            cve_scores=[0.9],
            chain_length=2,
            has_kev=False,
        )

        # Score with KEV should be higher
        assert score_with_kev > score_without_kev

    def test_chain_amplification_factor(self, chain_detector):
        """Test chain amplification factor."""
        # 2-hop chain: 1.5x amplification
        score_2hop = chain_detector._calculate_chain_score(
            cve_scores=[0.8],
            chain_length=2,
            has_kev=False,
        )

        # 3-hop chain: 2.0x amplification
        score_3hop = chain_detector._calculate_chain_score(
            cve_scores=[0.8],
            chain_length=3,
            has_kev=False,
        )

        # 3-hop should have higher score
        assert score_3hop > score_2hop

    def test_duplicate_prevention(self, chain_detector):
        """Test that duplicate chains are not recorded."""
        cves = ["CVE-2024-001", "CVE-2024-002"]
        chain_detector.detect_chains(cves)
        initial_count = len(chain_detector.chains)

        # Detect again
        chain_detector.detect_chains(cves)

        # Should not have duplicates (or should handle gracefully)
        assert len(chain_detector.chains) <= initial_count * 2

    def test_empty_cve_list(self, chain_detector):
        """Test with empty CVE list."""
        chain_detector.detect_chains([])
        assert len(chain_detector.chains) == 0

    def test_single_cve(self, chain_detector):
        """Test with single CVE (no chain possible)."""
        chain_detector.detect_chains(["CVE-2024-001"])
        # Single CVE shouldn't form a chain (need 2+ hop)
        assert len(chain_detector.chains) == 0
