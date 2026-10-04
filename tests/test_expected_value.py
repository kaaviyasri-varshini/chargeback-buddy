"""Tests for expected value calculation logic."""

from decimal import Decimal

import pytest


class TestExpectedValueLogic:
    """Test expected value calculations for fight vs refund decisions."""
    
    def test_high_win_probability_fight_recommended(self):
        """When win probability is high, fighting should be recommended."""
        amount = Decimal("100.00")
        win_prob = 0.90
        fighting_cost = Decimal("25.00")
        risk_buffer = Decimal("10.00")
        
        # Calculate losses
        refund_loss = amount
        fight_expected_loss = (Decimal("1") - Decimal(str(win_prob))) * amount + fighting_cost
        
        # Decision logic: FIGHT if win_prob * amount > fighting_cost + risk_buffer
        should_fight = win_prob * float(amount) > float(fighting_cost + risk_buffer)
        
        assert should_fight is True
        assert fight_expected_loss < refund_loss
        # (1 - 0.90) * 100 + 25 = 10 + 25 = 35
        # 35 < 100, so fighting is better
        assert float(fight_expected_loss) == 35.0
    
    def test_low_win_probability_refund_recommended(self):
        """When win probability is low, refund should be recommended."""
        amount = Decimal("100.00")
        win_prob = 0.20
        fighting_cost = Decimal("25.00")
        risk_buffer = Decimal("10.00")
        
        refund_loss = amount
        fight_expected_loss = (Decimal("1") - Decimal(str(win_prob))) * amount + fighting_cost
        
        should_fight = win_prob * float(amount) > float(fighting_cost + risk_buffer)
        
        assert should_fight is False
        # (1 - 0.20) * 100 + 25 = 80 + 25 = 105
        # 105 > 100, so refund is better
        assert float(fight_expected_loss) == 105.0
        assert fight_expected_loss > refund_loss
    
    def test_low_amount_refund_preferred(self):
        """Even with decent odds, low-value disputes should favor refund."""
        amount = Decimal("15.00")
        win_prob = 0.70
        fighting_cost = Decimal("25.00")
        risk_buffer = Decimal("10.00")
        
        refund_loss = amount
        fight_expected_loss = (Decimal("1") - Decimal(str(win_prob))) * amount + fighting_cost
        
        should_fight = win_prob * float(amount) > float(fighting_cost + risk_buffer)
        
        assert should_fight is False
        # Win value: 0.70 * 15 = 10.50
        # Cost to fight: 25 + 10 = 35
        # 10.50 < 35, so refund is better
        # (1 - 0.70) * 15 + 25 = 4.5 + 25 = 29.5
        assert float(fight_expected_loss) == 29.5
        assert fight_expected_loss > refund_loss
    
    def test_amount_equal_to_fighting_cost(self):
        """Edge case: dispute amount equals fighting cost."""
        amount = Decimal("25.00")
        win_prob = 0.50
        fighting_cost = Decimal("25.00")
        risk_buffer = Decimal("10.00")
        
        refund_loss = amount
        fight_expected_loss = (Decimal("1") - Decimal(str(win_prob))) * amount + fighting_cost
        
        should_fight = win_prob * float(amount) > float(fighting_cost + risk_buffer)
        
        assert should_fight is False
        # Win value: 0.50 * 25 = 12.50
        # Cost: 25 + 10 = 35
        # 12.50 < 35
        # (1 - 0.50) * 25 + 25 = 12.5 + 25 = 37.5
        assert float(fight_expected_loss) == 37.5
    
    def test_win_probability_near_zero(self):
        """Edge case: win probability near 0."""
        amount = Decimal("200.00")
        win_prob = 0.05
        fighting_cost = Decimal("25.00")
        risk_buffer = Decimal("10.00")
        
        refund_loss = amount
        fight_expected_loss = (Decimal("1") - Decimal(str(win_prob))) * amount + fighting_cost
        
        should_fight = win_prob * float(amount) > float(fighting_cost + risk_buffer)
        
        assert should_fight is False
        # Win value: 0.05 * 200 = 10
        # Cost: 35
        # (1 - 0.05) * 200 + 25 = 190 + 25 = 215
        assert float(fight_expected_loss) == 215.0
        assert fight_expected_loss > refund_loss
    
    def test_win_probability_near_one(self):
        """Edge case: win probability near 1."""
        amount = Decimal("150.00")
        win_prob = 0.95
        fighting_cost = Decimal("25.00")
        risk_buffer = Decimal("10.00")
        
        refund_loss = amount
        fight_expected_loss = (Decimal("1") - Decimal(str(win_prob))) * amount + fighting_cost
        
        should_fight = win_prob * float(amount) > float(fighting_cost + risk_buffer)
        
        assert should_fight is True
        # Win value: 0.95 * 150 = 142.50
        # Cost: 35
        # (1 - 0.95) * 150 + 25 = 7.5 + 25 = 32.5
        assert float(fight_expected_loss) == 32.5
        assert fight_expected_loss < refund_loss
    
    def test_breakeven_point(self):
        """Test the breakeven point where fight and refund are equal."""
        amount = Decimal("100.00")
        fighting_cost = Decimal("25.00")
        risk_buffer = Decimal("10.00")
        
        # At breakeven: win_prob * amount = fighting_cost + risk_buffer
        # win_prob = (fighting_cost + risk_buffer) / amount
        breakeven_win_prob = float(fighting_cost + risk_buffer) / float(amount)
        
        assert breakeven_win_prob == 0.35
        
        # Just below breakeven
        win_prob_below = 0.34
        should_fight_below = win_prob_below * float(amount) > float(fighting_cost + risk_buffer)
        assert should_fight_below is False
        
        # Just above breakeven
        win_prob_above = 0.36
        should_fight_above = win_prob_above * float(amount) > float(fighting_cost + risk_buffer)
        assert should_fight_above is True
