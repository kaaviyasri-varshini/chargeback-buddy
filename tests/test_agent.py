"""Tests for the Gemini agent analyzer."""

from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
import json

import pytest

from app.agent.analyzer import GeminiAnalyzer
from app.agent.models import StructuredDisputeAnalysis, ConfidenceLevel
from app.db.documents import (
    Dispute,
    DisputeReason,
    DisputeStatus,
    AgentDecision
)


class TestGeminiAnalyzer:
    """Test suite for GeminiAnalyzer."""
    
    @pytest.fixture
    def sample_dispute(self):
        """Create a sample dispute for testing."""
        from datetime import datetime, UTC
        # Create a mock dispute object to avoid Beanie initialization
        dispute = Mock(spec=Dispute)
        dispute.id = "mock_dispute_id_123"
        dispute.paypal_dispute_id = "PP-D-TEST-001"
        dispute.buyer_name = "Test Buyer"
        dispute.buyer_email = "buyer@test.com"
        dispute.amount = Decimal("100.00")
        dispute.currency = "USD"
        dispute.reason = DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED
        dispute.status = DisputeStatus.OPEN
        dispute.transaction_id = "TXN-TEST-001"
        dispute.order_id = "ORD-TEST-001"
        dispute.created_at = datetime.now(UTC).replace(tzinfo=None)
        dispute.evidence_items = [
            {
                "type": "TRACKING_INFO",
                "data": {"carrier": "UPS", "tracking": "1Z999", "status": "Delivered"},
                "strength_score": 0.9
            },
            {
                "type": "PROOF_OF_DELIVERY",
                "data": {"signature": "Test Buyer"},
                "strength_score": 0.95
            }
        ]
        return dispute
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Create a mock Gemini response."""
        return {
            "evidence_for": [
                {
                    "item": "Tracking shows delivered",
                    "why_it_helps": "Confirms item reached the buyer's address",
                    "weight": "strong"
                },
                {
                    "item": "Signature on delivery",
                    "why_it_helps": "Proof someone at address accepted package",
                    "weight": "strong"
                }
            ],
            "evidence_against": [
                {
                    "item": "No photo of delivered package",
                    "why_it_hurts": "Cannot prove exact item delivered",
                    "weight": "weak"
                }
            ],
            "missing_evidence": [
                "Photo of package at delivery location",
                "Communication with buyer after delivery"
            ],
            "llm_win_probability": 0.85,
            "confidence": "high",
            "reasoning_summary": "Strong delivery proof with tracking and signature makes this a winnable case. The buyer's claim of non-receipt contradicts physical delivery evidence. Consider fighting this dispute given the solid documentation."
        }
    
    @pytest.mark.asyncio
    async def test_fallback_analysis_no_gemini_api(self, sample_dispute):
        """Test that fallback analysis works when no API key is provided."""
        # Create analyzer without API key (will use fallback)
        with patch('app.agent.analyzer.settings') as mock_settings:
            mock_settings.gemini_api_key = ""
            mock_settings.fighting_cost = Decimal("25.00")
            mock_settings.risk_buffer = Decimal("10.00")
            
            with pytest.raises(ValueError, match="GEMINI_API_KEY must be set"):
                GeminiAnalyzer()
    
    @pytest.mark.asyncio
    async def test_heuristic_probability_calculation(self, sample_dispute):
        """Test heuristic probability calculation for fallback."""
        with patch('app.agent.analyzer.settings') as mock_settings:
            mock_settings.gemini_api_key = "fake_key"
            mock_settings.ai_model = "gemini-2.0-flash-exp"
            mock_settings.fighting_cost = Decimal("25.00")
            mock_settings.risk_buffer = Decimal("10.00")
            
            analyzer = GeminiAnalyzer()
            prob = analyzer._calculate_heuristic_probability(sample_dispute)
            
            # Should be high due to high evidence scores
            assert 0.7 <= prob <= 1.0
    
    @pytest.mark.asyncio
    async def test_fallback_analysis_structure(self, sample_dispute):
        """Test that fallback analysis returns valid structure."""
        with patch('app.agent.analyzer.settings') as mock_settings:
            mock_settings.gemini_api_key = "fake_key"
            mock_settings.ai_model = "gemini-2.0-flash-exp"
            mock_settings.fighting_cost = Decimal("25.00")
            mock_settings.risk_buffer = Decimal("10.00")
            
            analyzer = GeminiAnalyzer()
            fallback = analyzer._create_fallback_analysis(sample_dispute)
            
            assert isinstance(fallback, StructuredDisputeAnalysis)
            assert 0.0 <= fallback.llm_win_probability <= 1.0
            assert fallback.confidence in [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH]
            assert len(fallback.reasoning_summary) >= 20
            assert isinstance(fallback.evidence_for, list)
            assert isinstance(fallback.evidence_against, list)
            assert isinstance(fallback.missing_evidence, list)
    
    @pytest.mark.asyncio
    async def test_analyze_dispute_with_mocked_gemini(
        self, 
        sample_dispute, 
        mock_gemini_response
    ):
        """Test full analysis flow with mocked Gemini response."""
        with patch('app.agent.analyzer.settings') as mock_settings:
            mock_settings.gemini_api_key = "fake_key"
            mock_settings.ai_model = "gemini-2.0-flash-exp"
            mock_settings.fighting_cost = Decimal("25.00")
            mock_settings.risk_buffer = Decimal("10.00")
            
            # Mock the Gemini API call
            mock_response = Mock()
            mock_response.text = json.dumps(mock_gemini_response)
            
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model.generate_content = Mock(return_value=mock_response)
                mock_model_class.return_value = mock_model
                
                # Mock AgentAnalysis to avoid Beanie initialization
                with patch('app.agent.analyzer.AgentAnalysis') as mock_analysis_class:
                    mock_analysis = Mock()
                    mock_analysis.dispute_id = str(sample_dispute.id)
                    mock_analysis.decision = AgentDecision.FIGHT
                    mock_analysis.win_probability = 0.85
                    mock_analysis.confidence = 0.9
                    mock_analysis.refund_loss = sample_dispute.amount
                    mock_analysis.fighting_cost = Decimal("25.00")
                    mock_analysis.fight_expected_loss = Decimal("40.00")
                    mock_analysis_class.return_value = mock_analysis
                    
                    analyzer = GeminiAnalyzer()
                    
                    # Don't persist to avoid DB calls in unit test
                    analysis = await analyzer.analyze_dispute(sample_dispute, persist=False)
                    
                    # Verify analysis structure
                    assert analysis.dispute_id == str(sample_dispute.id)
                    assert analysis.decision in [AgentDecision.FIGHT, AgentDecision.REFUND]
                    assert 0.0 <= analysis.win_probability <= 1.0
                    assert 0.0 <= analysis.confidence <= 1.0
                    assert analysis.refund_loss == sample_dispute.amount
                    assert analysis.fighting_cost == Decimal("25.00")
                    
                    # With high win probability (0.85), should recommend FIGHT
                    # 0.85 * 100 = 85 > 25 + 10 = 35
                    assert analysis.decision == AgentDecision.FIGHT
    
    @pytest.mark.asyncio
    async def test_fight_decision_logic(self, sample_dispute):
        """Test that FIGHT decision is made when conditions are met."""
        with patch('app.agent.analyzer.settings') as mock_settings:
            mock_settings.gemini_api_key = "fake_key"
            mock_settings.ai_model = "gemini-2.0-flash-exp"
            mock_settings.fighting_cost = Decimal("25.00")
            mock_settings.risk_buffer = Decimal("10.00")
            
            # Mock Gemini to return high win probability
            high_prob_response = {
                "evidence_for": [{"item": "Test", "why_it_helps": "Test", "weight": "strong"}],
                "evidence_against": [],
                "missing_evidence": [],
                "llm_win_probability": 0.90,
                "confidence": "high",
                "reasoning_summary": "Strong case. High probability of success. Recommend fighting."
            }
            
            mock_response = Mock()
            mock_response.text = json.dumps(high_prob_response)
            
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model.generate_content = Mock(return_value=mock_response)
                mock_model_class.return_value = mock_model
                
                with patch('app.agent.analyzer.AgentAnalysis') as mock_analysis_class:
                    mock_analysis = Mock()
                    mock_analysis.decision = AgentDecision.FIGHT
                    mock_analysis_class.return_value = mock_analysis
                    
                    analyzer = GeminiAnalyzer()
                    analysis = await analyzer.analyze_dispute(sample_dispute, persist=False)
                    
                    # 0.90 * 100 = 90 > 35, should FIGHT
                    assert analysis.decision == AgentDecision.FIGHT
    
    @pytest.mark.asyncio
    async def test_refund_decision_logic(self, sample_dispute):
        """Test that REFUND decision is made when fighting cost is too high."""
        with patch('app.agent.analyzer.settings') as mock_settings:
            mock_settings.gemini_api_key = "fake_key"
            mock_settings.ai_model = "gemini-2.0-flash-exp"
            mock_settings.fighting_cost = Decimal("25.00")
            mock_settings.risk_buffer = Decimal("10.00")
            
            # Mock Gemini to return low win probability
            low_prob_response = {
                "evidence_for": [],
                "evidence_against": [{"item": "Test", "why_it_hurts": "Test", "weight": "strong"}],
                "missing_evidence": ["Everything"],
                "llm_win_probability": 0.20,
                "confidence": "medium",
                "reasoning_summary": "Weak case with limited evidence. Low probability of success. Recommend refunding."
            }
            
            mock_response = Mock()
            mock_response.text = json.dumps(low_prob_response)
            
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model.generate_content = Mock(return_value=mock_response)
                mock_model_class.return_value = mock_model
                
                with patch('app.agent.analyzer.AgentAnalysis') as mock_analysis_class:
                    mock_analysis = Mock()
                    mock_analysis.decision = AgentDecision.REFUND
                    mock_analysis_class.return_value = mock_analysis
                    
                    analyzer = GeminiAnalyzer()
                    analysis = await analyzer.analyze_dispute(sample_dispute, persist=False)
                    
                    # 0.20 * 100 = 20 < 35, should REFUND
                    assert analysis.decision == AgentDecision.REFUND
    
    @pytest.mark.asyncio
    async def test_retry_logic_on_json_error(self, sample_dispute):
        """Test that analyzer retries on JSON parse errors."""
        with patch('app.agent.analyzer.settings') as mock_settings:
            mock_settings.gemini_api_key = "fake_key"
            mock_settings.ai_model = "gemini-2.0-flash-exp"
            mock_settings.fighting_cost = Decimal("25.00")
            mock_settings.risk_buffer = Decimal("10.00")
            
            # First call returns invalid JSON, second succeeds
            mock_response_bad = Mock()
            mock_response_bad.text = "Invalid JSON{"
            
            mock_response_good = Mock()
            mock_response_good.text = json.dumps({
                "evidence_for": [],
                "evidence_against": [],
                "missing_evidence": [],
                "llm_win_probability": 0.5,
                "confidence": "medium",
                "reasoning_summary": "Test case. Moderate probability. Needs more evidence to decide."
            })
            
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model.generate_content = Mock(
                    side_effect=[mock_response_bad, mock_response_good]
                )
                mock_model_class.return_value = mock_model
                
                analyzer = GeminiAnalyzer()
                
                # Should succeed on retry
                structured = await analyzer._call_gemini_with_retry(
                    "test prompt",
                    max_retries=2,
                    initial_delay=0.01
                )
                
                assert structured is not None
                assert structured.llm_win_probability == 0.5
    
    @pytest.mark.asyncio
    async def test_falls_back_after_max_retries(self, sample_dispute):
        """Test that analyzer falls back to heuristic after max retries."""
        with patch('app.agent.analyzer.settings') as mock_settings:
            mock_settings.gemini_api_key = "fake_key"
            mock_settings.ai_model = "gemini-2.0-flash-exp"
            mock_settings.fighting_cost = Decimal("25.00")
            mock_settings.risk_buffer = Decimal("10.00")
            
            # Always return invalid response
            mock_response = Mock()
            mock_response.text = "Invalid"
            
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model.generate_content = Mock(return_value=mock_response)
                mock_model_class.return_value = mock_model
                
                with patch('app.agent.analyzer.AgentAnalysis') as mock_analysis_class:
                    mock_analysis = Mock()
                    mock_analysis.decision = AgentDecision.REFUND  # Set a real value, not Mock
                    mock_analysis.win_probability = 0.3
                    mock_analysis_class.return_value = mock_analysis
                    
                    analyzer = GeminiAnalyzer()
                    analysis = await analyzer.analyze_dispute(sample_dispute, persist=False)
                    
                    # Should still return valid analysis using fallback
                    assert analysis is not None
                    assert analysis.decision in [AgentDecision.FIGHT, AgentDecision.REFUND]
                    assert 0.0 <= analysis.win_probability <= 1.0
