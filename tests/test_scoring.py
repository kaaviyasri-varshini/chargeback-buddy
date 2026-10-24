"""Tests for heuristic scoring system."""

from datetime import datetime, timedelta, UTC
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.agent.scoring import (
    calculate_heuristic_probability,
    blend_probabilities,
    explain_heuristic_score,
    BASE_RATES,
    FEATURE_WEIGHTS
)
from app.db.documents import DisputeReason


class TestHeuristicScoring:
    """Test suite for heuristic scoring."""
    
    @pytest.fixture
    def mock_dispute(self):
        """Create a mock dispute."""
        dispute = Mock()
        dispute.id = "test_id"
        dispute.reason = DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED
        dispute.amount = Decimal("100.00")
        dispute.created_at = datetime.now(UTC).replace(tzinfo=None)
        dispute.evidence_items = []
        return dispute
    
    def test_base_rate_only(self, mock_dispute):
        """Test that base rate is used when no evidence is provided."""
        prob = calculate_heuristic_probability(mock_dispute)
        
        # Should be close to base rate with minimal evidence penalty
        base = BASE_RATES[DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED]
        minimal_penalty = FEATURE_WEIGHTS["evidence_minimal"]
        
        expected = base + minimal_penalty
        # Allow for transaction age and other minor factors
        assert abs(prob - expected) < 0.05
    
    def test_tracking_increases_probability(self, mock_dispute):
        """Test that tracking evidence increases win probability."""
        prob_without = calculate_heuristic_probability(mock_dispute)
        
        # Add tracking
        mock_dispute.evidence_items = [
            {
                "type": "TRACKING_INFO",
                "data": {"carrier": "UPS", "tracking": "123", "status": "Delivered"},
                "strength_score": 0.9
            }
        ]
        
        prob_with = calculate_heuristic_probability(mock_dispute)
        
        # Should increase
        assert prob_with > prob_without
    
    def test_proof_of_delivery_increases_probability(self, mock_dispute):
        """Test that proof of delivery increases win probability."""
        mock_dispute.evidence_items = [
            {
                "type": "PROOF_OF_DELIVERY",
                "data": {"signature": "John Doe"},
                "strength_score": 0.95
            }
        ]
        
        prob = calculate_heuristic_probability(mock_dispute)
        base = BASE_RATES[DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED]
        
        # Should be higher than base
        assert prob > base
    
    def test_multiple_evidence_increases_probability(self, mock_dispute):
        """Test that multiple pieces of evidence compound."""
        mock_dispute.evidence_items = [
            {
                "type": "TRACKING_INFO",
                "data": {"carrier": "UPS", "tracking": "123", "status": "Delivered"},
                "strength_score": 0.9
            },
            {
                "type": "PROOF_OF_DELIVERY",
                "data": {"signature": "John Doe"},
                "strength_score": 0.95
            },
            {
                "type": "BUYER_COMMUNICATION",
                "data": {"messages": 3, "tone": "professional"},
                "strength_score": 0.7
            },
            {
                "type": "PHOTOS",
                "data": {"count": 2},
                "strength_score": 0.8
            }
        ]
        
        prob = calculate_heuristic_probability(mock_dispute)
        base = BASE_RATES[DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED]
        
        # Should be significantly higher with complete evidence
        assert prob > base + 0.2
    
    def test_high_value_dispute_decreases_probability(self, mock_dispute):
        """Test that high-value disputes are slightly harder."""
        mock_dispute.amount = Decimal("50.00")
        prob_low = calculate_heuristic_probability(mock_dispute)
        
        mock_dispute.amount = Decimal("500.00")
        prob_high = calculate_heuristic_probability(mock_dispute)
        
        # High value should be slightly lower
        assert prob_high < prob_low
    
    def test_low_value_dispute_increases_probability(self, mock_dispute):
        """Test that low-value disputes are slightly easier."""
        mock_dispute.amount = Decimal("25.00")
        prob_low = calculate_heuristic_probability(mock_dispute)
        
        mock_dispute.amount = Decimal("100.00")
        prob_mid = calculate_heuristic_probability(mock_dispute)
        
        # Low value should be slightly higher
        assert prob_low > prob_mid
    
    def test_clamping_to_range(self, mock_dispute):
        """Test that probabilities are clamped to valid range."""
        # Test with no evidence (should not go below min)
        prob_min = calculate_heuristic_probability(mock_dispute, min_prob=0.05, max_prob=0.95)
        assert 0.05 <= prob_min <= 0.95
        
        # Test with maximum evidence
        mock_dispute.evidence_items = [
            {"type": "TRACKING_INFO", "data": {"status": "Delivered"}, "strength_score": 0.95},
            {"type": "PROOF_OF_DELIVERY", "data": {"signature": "X"}, "strength_score": 0.95},
            {"type": "BUYER_COMMUNICATION", "data": {"tone": "professional"}, "strength_score": 0.9},
            {"type": "PHOTOS", "data": {}, "strength_score": 0.9},
            {"type": "ITEM_DESCRIPTION", "data": {}, "strength_score": 0.85},
        ]
        prob_max = calculate_heuristic_probability(mock_dispute, min_prob=0.05, max_prob=0.95)
        assert 0.05 <= prob_max <= 0.95
    
    def test_unauthorized_dispute_low_base_rate(self, mock_dispute):
        """Test that unauthorized disputes have a low base rate."""
        mock_dispute.reason = DisputeReason.UNAUTHORISED
        prob = calculate_heuristic_probability(mock_dispute)
        
        # Should be low even with adjustments
        assert prob < 0.3
    
    def test_duplicate_transaction_high_base_rate(self, mock_dispute):
        """Test that duplicate transaction disputes have a higher base rate."""
        mock_dispute.reason = DisputeReason.DUPLICATE_TRANSACTION
        mock_dispute.evidence_items = [
            {"type": "INVOICE", "data": {}, "strength_score": 0.9}
        ]
        prob = calculate_heuristic_probability(mock_dispute)
        
        # Should be relatively high (with one evidence item, lower than if 4+)
        assert prob > 0.45  # Base is 0.6, minus recent transaction, minimal evidence penalty
    
    def test_monotonicity_with_evidence(self, mock_dispute):
        """Test that adding evidence never decreases probability."""
        # Start with no evidence
        prob_0 = calculate_heuristic_probability(mock_dispute)
        
        # Add one piece
        mock_dispute.evidence_items = [
            {"type": "TRACKING_INFO", "data": {"status": "Delivered"}, "strength_score": 0.9}
        ]
        prob_1 = calculate_heuristic_probability(mock_dispute)
        
        # Add another
        mock_dispute.evidence_items.append(
            {"type": "PROOF_OF_DELIVERY", "data": {"signature": "X"}, "strength_score": 0.9}
        )
        prob_2 = calculate_heuristic_probability(mock_dispute)
        
        # Should be monotonically increasing (or at least not decreasing)
        assert prob_1 >= prob_0
        assert prob_2 >= prob_1


class TestProbabilityBlending:
    """Test suite for probability blending."""
    
    def test_equal_weights(self):
        """Test blending with equal weights."""
        heuristic = 0.6
        llm = 0.8
        
        blended = blend_probabilities(heuristic, llm, heuristic_weight=0.5, llm_weight=0.5)
        
        # Should be average
        assert abs(blended - 0.7) < 0.001
    
    def test_heuristic_dominated(self):
        """Test blending with heuristic-dominated weights."""
        heuristic = 0.6
        llm = 0.9
        
        blended = blend_probabilities(heuristic, llm, heuristic_weight=0.8, llm_weight=0.2)
        
        # Should be closer to heuristic
        assert abs(blended - 0.66) < 0.01
    
    def test_llm_dominated(self):
        """Test blending with LLM-dominated weights."""
        heuristic = 0.4
        llm = 0.8
        
        blended = blend_probabilities(heuristic, llm, heuristic_weight=0.2, llm_weight=0.8)
        
        # Should be closer to LLM
        assert abs(blended - 0.72) < 0.01
    
    def test_default_weights(self):
        """Test default 60/40 split."""
        heuristic = 0.5
        llm = 0.9
        
        blended = blend_probabilities(heuristic, llm)  # Default 0.6/0.4
        
        # Should be 0.5 * 0.6 + 0.9 * 0.4 = 0.66
        assert abs(blended - 0.66) < 0.001
    
    def test_zero_weights_fallback(self):
        """Test that zero weights return fallback."""
        heuristic = 0.5
        llm = 0.9
        
        blended = blend_probabilities(heuristic, llm, heuristic_weight=0.0, llm_weight=0.0)
        
        # Should return fallback
        assert blended == 0.5
    
    def test_blending_math_correctness(self):
        """Test blending formula correctness."""
        h = 0.7
        l = 0.3
        hw = 0.6
        lw = 0.4
        
        blended = blend_probabilities(h, l, hw, lw)
        expected = (hw * h + lw * l) / (hw + lw)
        
        assert abs(blended - expected) < 0.0001


class TestScoringExplanation:
    """Test suite for scoring explanation."""
    
    @pytest.fixture
    def mock_dispute(self):
        """Create a mock dispute with evidence."""
        dispute = Mock()
        dispute.id = "test_id"
        dispute.reason = DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED
        dispute.amount = Decimal("100.00")
        dispute.created_at = datetime.now(UTC).replace(tzinfo=None)
        dispute.evidence_items = [
            {"type": "TRACKING_INFO", "data": {"status": "Delivered"}, "strength_score": 0.9},
            {"type": "PROOF_OF_DELIVERY", "data": {"signature": "X"}, "strength_score": 0.95}
        ]
        return dispute
    
    def test_explanation_structure(self, mock_dispute):
        """Test that explanation has expected structure."""
        explanation = explain_heuristic_score(mock_dispute)
        
        assert "base_rate" in explanation
        assert "adjustments" in explanation
        assert "final_score" in explanation
        
        assert "reason" in explanation["base_rate"]
        assert "rate" in explanation["base_rate"]
        assert isinstance(explanation["adjustments"], list)
        assert isinstance(explanation["final_score"], float)
    
    def test_explanation_includes_base_rate(self, mock_dispute):
        """Test that explanation includes base rate."""
        explanation = explain_heuristic_score(mock_dispute)
        
        base_rate = BASE_RATES[DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED]
        assert explanation["base_rate"]["rate"] == base_rate
    
    def test_explanation_includes_adjustments(self, mock_dispute):
        """Test that explanation includes adjustments."""
        explanation = explain_heuristic_score(mock_dispute)
        
        # Should have adjustments for tracking and proof of delivery
        assert len(explanation["adjustments"]) >= 2
        
        # Check that adjustments have proper structure
        for adj in explanation["adjustments"]:
            assert "factor" in adj
            assert "adjustment" in adj
            assert "impact" in adj
    
    def test_explanation_final_score_matches_calculation(self, mock_dispute):
        """Test that explanation final score matches actual calculation."""
        explanation = explain_heuristic_score(mock_dispute)
        calculated = calculate_heuristic_probability(mock_dispute)
        
        assert abs(explanation["final_score"] - calculated) < 0.0001
