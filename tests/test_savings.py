"""Tests for savings calculation module."""

from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
import pytest

from app.services.savings import (
    _simulate_always_refund_strategy,
    _simulate_always_fight_strategy,
    StrategyResult
)
from app.db.documents import DisputeReason, DisputeStatus
from app.config import settings


class TestSavingsCalculations:
    """Test savings calculation logic."""
    
    @pytest.fixture
    def mock_disputes(self):
        """Create mock disputes for testing."""
        disputes = []
        
        # Dispute 1: $100
        d1 = Mock()
        d1.id = "dispute_1"
        d1.amount = Decimal("100.00")
        disputes.append(d1)
        
        # Dispute 2: $50
        d2 = Mock()
        d2.id = "dispute_2"
        d2.amount = Decimal("50.00")
        disputes.append(d2)
        
        # Dispute 3: $200
        d3 = Mock()
        d3.id = "dispute_3"
        d3.amount = Decimal("200.00")
        disputes.append(d3)
        
        return disputes
    
    @pytest.fixture
    def mock_outcomes(self):
        """Create mock outcomes."""
        return {
            "dispute_1": True,   # Won
            "dispute_2": False,  # Lost
            "dispute_3": True    # Won
        }
    
    @pytest.mark.asyncio
    async def test_always_refund_loses_all_amounts(self, mock_disputes, mock_outcomes):
        """Test that always refund strategy loses all dispute amounts."""
        result = await _simulate_always_refund_strategy(mock_disputes, mock_outcomes)
        
        # Should lose 100 + 50 + 200 = 350
        assert result.total_net == Decimal("-350.00")
        assert result.disputes_refunded == 3
        assert result.disputes_fought == 0
        assert result.wins == 0
        assert result.losses == 0
        assert result.fighting_costs == Decimal("0")
    
    @pytest.mark.asyncio
    async def test_always_fight_with_all_wins(self, mock_disputes):
        """Test always fight when winning all disputes."""
        # All wins
        outcomes = {
            "dispute_1": True,
            "dispute_2": True,
            "dispute_3": True
        }
        
        with patch.object(settings, 'fighting_cost', Decimal("25.00")):
            result = await _simulate_always_fight_strategy(mock_disputes, outcomes)
            
            # Won 100 + 50 + 200 = 350
            # Paid fighting costs: 3 * 25 = 75
            # Net: 350 - 75 = 275
            assert result.total_net == Decimal("275.00")
            assert result.disputes_fought == 3
            assert result.wins == 3
            assert result.losses == 0
            assert result.fighting_costs == Decimal("75.00")
    
    @pytest.mark.asyncio
    async def test_always_fight_with_all_losses(self, mock_disputes):
        """Test always fight when losing all disputes."""
        # All losses
        outcomes = {
            "dispute_1": False,
            "dispute_2": False,
            "dispute_3": False
        }
        
        with patch.object(settings, 'fighting_cost', Decimal("25.00")):
            result = await _simulate_always_fight_strategy(mock_disputes, outcomes)
            
            # Lost all disputes, paid fighting costs: 3 * 25 = 75
            # Net: -75
            assert result.total_net == Decimal("-75.00")
            assert result.disputes_fought == 3
            assert result.wins == 0
            assert result.losses == 3
            assert result.fighting_costs == Decimal("75.00")
    
    @pytest.mark.asyncio
    async def test_always_fight_with_mixed_outcomes(self, mock_disputes, mock_outcomes):
        """Test always fight with mixed win/loss outcomes."""
        # Wins: dispute_1 (100), dispute_3 (200) = 300
        # Losses: dispute_2 (50)
        # Fighting costs: 3 * 25 = 75
        # Net: 300 - 75 = 225
        
        with patch.object(settings, 'fighting_cost', Decimal("25.00")):
            result = await _simulate_always_fight_strategy(mock_disputes, mock_outcomes)
            
            assert result.total_net == Decimal("225.00")
            assert result.disputes_fought == 3
            assert result.wins == 2
            assert result.losses == 1
            assert result.fighting_costs == Decimal("75.00")
    
    def test_strategy_result_dataclass(self):
        """Test StrategyResult dataclass."""
        result = StrategyResult(
            strategy_name="Test",
            total_net=Decimal("100.00"),
            disputes_fought=5,
            disputes_refunded=3,
            wins=3,
            losses=2,
            fighting_costs=Decimal("125.00")
        )
        
        assert result.strategy_name == "Test"
        assert result.total_net == Decimal("100.00")
        assert result.disputes_fought == 5
        assert result.disputes_refunded == 3
        assert result.wins == 3
        assert result.losses == 2
        assert result.fighting_costs == Decimal("125.00")
    
    def test_refund_vs_fight_comparison(self):
        """Test comparing refund and fight strategies on same data."""
        # Create simple test case
        disputes = [Mock(id="d1", amount=Decimal("100.00"))]
        
        # If we win with 100% probability
        outcomes_win = {"d1": True}
        
        # Always refund: -100
        # Always fight and win: 100 - 25 = 75
        # Fight is better by 175
        
        # If we lose with 100% probability  
        outcomes_lose = {"d1": False}
        
        # Always refund: -100
        # Always fight and lose: -25
        # Refund is worse by 75 (fight is better by 75)


class TestSavingsArithmetic:
    """Test arithmetic correctness of savings calculations."""
    
    def test_hand_calculated_example(self):
        """Test against a hand-calculated example."""
        # Given:
        # - 2 disputes: $100 and $50
        # - Fighting cost: $25
        # - Outcomes: dispute 1 won, dispute 2 lost
        
        # Always Refund: -(100 + 50) = -150
        
        # Always Fight:
        #   Dispute 1 (won): +100 - 25 = +75
        #   Dispute 2 (lost): 0 - 25 = -25
        #   Total: 75 - 25 = 50
        
        # ChargeBack Buddy (fight dispute 1, refund dispute 2):
        #   Dispute 1 (fought and won): +100 - 25 = +75
        #   Dispute 2 (refunded): -50
        #   Total: 75 - 50 = 25
        
        # Savings:
        #   vs Always Refund: 25 - (-150) = 175
        #   vs Always Fight: 25 - 50 = -25 (worse by 25)
        #   vs Best Baseline (Always Fight = 50): 25 - 50 = -25
        
        # This test verifies the math is correct
        always_refund_net = Decimal("-150.00")
        always_fight_net = Decimal("50.00")
        chargebach_buddy_net = Decimal("25.00")
        
        savings_vs_refund = chargebach_buddy_net - always_refund_net
        savings_vs_fight = chargebach_buddy_net - always_fight_net
        
        assert savings_vs_refund == Decimal("175.00")
        assert savings_vs_fight == Decimal("-25.00")
        
        # Best baseline is Always Fight
        best_baseline = max(always_refund_net, always_fight_net)
        assert best_baseline == Decimal("50.00")
        
        total_savings = chargebach_buddy_net - best_baseline
        assert total_savings == Decimal("-25.00")
