"""Calculate concrete savings from AI recommendations.

This module computes savings by comparing ChargeBack Buddy's recommendations
against baseline strategies (always refund, always fight).

NOTE: This uses simulated outcomes for demonstration purposes.
In production, you would track actual PayPal resolutions.
"""

import argparse
import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Tuple
from dataclasses import dataclass

from app.db.connection import init_db, close_db
from app.db.documents import Dispute, AgentAnalysis, AgentDecision
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """Results from a dispute resolution strategy."""
    strategy_name: str
    total_net: Decimal  # Net money (positive = saved, negative = lost)
    disputes_fought: int
    disputes_refunded: int
    wins: int
    losses: int
    fighting_costs: Decimal
    

async def calculate_savings() -> Dict[str, any]:
    """
    Calculate savings across all analyzed disputes.
    
    Returns:
        Dictionary with savings calculations
    """
    logger.info("Calculating savings from AI recommendations...")
    
    # Get all disputes with analyses
    disputes = await Dispute.find().to_list()
    
    if not disputes:
        logger.warning("No disputes found")
        return {
            "total_disputes": 0,
            "chargebach_buddy": None,
            "always_refund": None,
            "always_fight": None,
            "savings_vs_refund": Decimal("0"),
            "savings_vs_fight": Decimal("0")
        }
    
    # Get ground truth outcomes
    outcomes = await _get_simulated_outcomes(disputes)
    
    # Simulate each strategy
    chargebach_buddy = await _simulate_chargebach_buddy_strategy(disputes, outcomes)
    always_refund = await _simulate_always_refund_strategy(disputes, outcomes)
    always_fight = await _simulate_always_fight_strategy(disputes, outcomes)
    
    # Calculate savings
    savings_vs_refund = chargebach_buddy.total_net - always_refund.total_net
    savings_vs_fight = chargebach_buddy.total_net - always_fight.total_net
    
    logger.info(f"ChargeBack Buddy net: ${chargebach_buddy.total_net:.2f}")
    logger.info(f"Always Refund net: ${always_refund.total_net:.2f}")
    logger.info(f"Always Fight net: ${always_fight.total_net:.2f}")
    logger.info(f"Savings vs Always Refund: ${savings_vs_refund:.2f}")
    logger.info(f"Savings vs Always Fight: ${savings_vs_fight:.2f}")
    
    return {
        "total_disputes": len(disputes),
        "chargebach_buddy": chargebach_buddy,
        "always_refund": always_refund,
        "always_fight": always_fight,
        "savings_vs_refund": savings_vs_refund,
        "savings_vs_fight": savings_vs_fight
    }


async def _get_simulated_outcomes(disputes: List[Dispute]) -> Dict[str, bool]:
    """
    Generate simulated dispute outcomes based on features.
    
    NOTE: This is SIMULATED data for demonstration. In production,
    you would track actual PayPal resolution outcomes.
    
    Args:
        disputes: List of disputes to generate outcomes for
        
    Returns:
        Dictionary mapping dispute_id to win/loss (True = seller won)
    """
    import random
    from app.agent.scoring import calculate_heuristic_probability
    
    # Use fixed seed for reproducibility
    random.seed(42)
    
    outcomes = {}
    
    for dispute in disputes:
        # Get the heuristic probability (feature-based estimate)
        win_prob = calculate_heuristic_probability(dispute)
        
        # Simulate outcome: weighted random draw
        # Higher quality evidence = higher chance of winning
        won = random.random() < win_prob
        
        outcomes[str(dispute.id)] = won
        
        logger.debug(f"Dispute {dispute.paypal_dispute_id}: win_prob={win_prob:.2f}, won={won}")
    
    return outcomes


async def _simulate_chargebach_buddy_strategy(
    disputes: List[Dispute],
    outcomes: Dict[str, bool]
) -> StrategyResult:
    """
    Simulate following ChargeBack Buddy's recommendations.
    
    Args:
        disputes: List of disputes
        outcomes: Ground truth outcomes
        
    Returns:
        Strategy results
    """
    total_net = Decimal("0")
    fought = 0
    refunded = 0
    wins = 0
    losses = 0
    fighting_costs = Decimal("0")
    
    for dispute in disputes:
        # Get the AI recommendation
        if dispute.latest_analysis_id:
            try:
                analysis = await AgentAnalysis.get(dispute.latest_analysis_id)
            except:
                logger.warning(f"Could not find analysis for dispute {dispute.id}")
                continue
        else:
            continue
        
        won = outcomes.get(str(dispute.id), False)
        
        if analysis.decision == AgentDecision.FIGHT:
            fought += 1
            fighting_costs += settings.fighting_cost
            
            if won:
                wins += 1
                # Won: keep the money, pay fighting cost
                total_net += dispute.amount - settings.fighting_cost
            else:
                losses += 1
                # Lost: lose money and pay fighting cost
                total_net -= settings.fighting_cost
        else:
            # REFUND
            refunded += 1
            # Refunded: lose the dispute amount
            total_net -= dispute.amount
    
    return StrategyResult(
        strategy_name="ChargeBack Buddy",
        total_net=total_net,
        disputes_fought=fought,
        disputes_refunded=refunded,
        wins=wins,
        losses=losses,
        fighting_costs=fighting_costs
    )


async def _simulate_always_refund_strategy(
    disputes: List[Dispute],
    outcomes: Dict[str, bool]
) -> StrategyResult:
    """
    Simulate always refunding every dispute.
    
    Args:
        disputes: List of disputes
        outcomes: Ground truth outcomes (not used, but kept for interface consistency)
        
    Returns:
        Strategy results
    """
    total_net = Decimal("0")
    
    for dispute in disputes:
        # Always refund: lose the dispute amount
        total_net -= dispute.amount
    
    return StrategyResult(
        strategy_name="Always Refund",
        total_net=total_net,
        disputes_fought=0,
        disputes_refunded=len(disputes),
        wins=0,
        losses=0,
        fighting_costs=Decimal("0")
    )


async def _simulate_always_fight_strategy(
    disputes: List[Dispute],
    outcomes: Dict[str, bool]
) -> StrategyResult:
    """
    Simulate always fighting every dispute.
    
    Args:
        disputes: List of disputes
        outcomes: Ground truth outcomes
        
    Returns:
        Strategy results
    """
    total_net = Decimal("0")
    wins = 0
    losses = 0
    fighting_costs = Decimal("0")
    
    for dispute in disputes:
        won = outcomes.get(str(dispute.id), False)
        fighting_costs += settings.fighting_cost
        
        if won:
            wins += 1
            # Won: keep the money, pay fighting cost
            total_net += dispute.amount - settings.fighting_cost
        else:
            losses += 1
            # Lost: lose money and pay fighting cost
            total_net -= settings.fighting_cost
    
    return StrategyResult(
        strategy_name="Always Fight",
        total_net=total_net,
        disputes_fought=len(disputes),
        disputes_refunded=0,
        wins=wins,
        losses=losses,
        fighting_costs=fighting_costs
    )


def format_savings_report(results: Dict[str, any]) -> str:
    """
    Format savings results as a readable report.
    
    Args:
        results: Results from calculate_savings()
        
    Returns:
        Formatted report string
    """
    if results["total_disputes"] == 0:
        return "No disputes found. Run seeding first: python -m app.db.seed"
    
    cb = results["chargebach_buddy"]
    refund = results["always_refund"]
    fight = results["always_fight"]
    
    report = []
    report.append("\n" + "="*80)
    report.append(" ChargeBack Buddy Savings Analysis")
    report.append("="*80)
    report.append("")
    report.append(f"Total Disputes Analyzed: {results['total_disputes']}")
    report.append("")
    report.append("NOTE: This analysis uses SIMULATED outcomes based on dispute features.")
    report.append("      In production, track actual PayPal resolutions.")
    report.append("")
    report.append("-" * 80)
    report.append(" Strategy Comparison")
    report.append("-" * 80)
    report.append("")
    
    # ChargeBack Buddy
    report.append(f"📊 ChargeBack Buddy (AI-Powered):")
    report.append(f"   • Fought: {cb.disputes_fought} disputes (won {cb.wins}, lost {cb.losses})")
    report.append(f"   • Refunded: {cb.disputes_refunded} disputes")
    report.append(f"   • Fighting costs: ${cb.fighting_costs:.2f}")
    report.append(f"   • Net result: ${cb.total_net:.2f}")
    report.append("")
    
    # Always Refund
    report.append(f"💰 Always Refund (Baseline):")
    report.append(f"   • Refunded: {refund.disputes_refunded} disputes")
    report.append(f"   • Net result: ${refund.total_net:.2f}")
    report.append("")
    
    # Always Fight
    report.append(f"⚔️  Always Fight (Baseline):")
    report.append(f"   • Fought: {fight.disputes_fought} disputes (won {fight.wins}, lost {fight.losses})")
    report.append(f"   • Fighting costs: ${fight.fighting_costs:.2f}")
    report.append(f"   • Net result: ${fight.total_net:.2f}")
    report.append("")
    
    report.append("-" * 80)
    report.append(" Savings Summary")
    report.append("-" * 80)
    report.append("")
    
    savings_refund = results["savings_vs_refund"]
    savings_fight = results["savings_vs_fight"]
    
    if savings_refund > 0:
        report.append(f"✅ ChargeBack Buddy saved ${savings_refund:.2f} vs Always Refund")
    else:
        report.append(f"⚠️  ChargeBack Buddy lost ${abs(savings_refund):.2f} vs Always Refund")
    
    if savings_fight > 0:
        report.append(f"✅ ChargeBack Buddy saved ${savings_fight:.2f} vs Always Fight")
    else:
        report.append(f"⚠️  ChargeBack Buddy lost ${abs(savings_fight):.2f} vs Always Fight")
    
    report.append("")
    
    # Best baseline
    best_baseline = max(refund.total_net, fight.total_net)
    total_savings = cb.total_net - best_baseline
    best_name = "Always Refund" if refund.total_net > fight.total_net else "Always Fight"
    
    report.append(f"💡 Best Baseline: {best_name} (${best_baseline:.2f})")
    if total_savings > 0:
        report.append(f"🎉 ChargeBack Buddy Improvement: ${total_savings:.2f}")
    else:
        report.append(f"⚠️  ChargeBack Buddy vs Best Baseline: ${total_savings:.2f}")
    
    report.append("")
    report.append("="*80)
    report.append("")
    
    return "\n".join(report)


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Calculate savings from AI recommendations")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    try:
        await init_db()
        results = await calculate_savings()
        
        if args.json:
            import json
            # Convert Decimals to strings for JSON
            json_results = {
                "total_disputes": results["total_disputes"],
                "savings_vs_refund": str(results["savings_vs_refund"]),
                "savings_vs_fight": str(results["savings_vs_fight"])
            }
            print(json.dumps(json_results, indent=2))
        else:
            print(format_savings_report(results))
    
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
