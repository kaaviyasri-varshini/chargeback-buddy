"""Heuristic-based win probability scorer for disputes.

This module provides a transparent, rule-based scoring system that doesn't
rely solely on the LLM. It uses dispute features and evidence to estimate
win probability independently, which is then blended with LLM estimates.
"""

from decimal import Decimal
from typing import Optional

from app.db.documents import Dispute, DisputeReason


# Base win rates by dispute reason
# NOTE: These are ASSUMPTIONS based on general industry knowledge, not PayPal statistics
BASE_RATES = {
    DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED: 0.45,  # Tracking helps a lot
    DisputeReason.MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED: 0.35,  # Subjective, buyer-favored
    DisputeReason.UNAUTHORISED: 0.10,  # Very hard to fight
    DisputeReason.CREDIT_NOT_PROCESSED: 0.40,  # Depends on proof of refund
    DisputeReason.DUPLICATE_TRANSACTION: 0.60,  # Easy with transaction records
    DisputeReason.INCORRECT_AMOUNT: 0.55,  # Clear with invoice
    DisputeReason.PAYMENT_BY_OTHER_MEANS: 0.50,  # Moderate with proof
    DisputeReason.CANCELED_RECURRING_BILLING: 0.45,  # Depends on cancellation terms
    DisputeReason.PROBLEM_WITH_REMITTANCE: 0.40,  # Complex
    DisputeReason.OTHER: 0.35,  # Conservative estimate for unknown
}


# Feature weights (adjustment to base rate)
# These are clearly documented for transparency and easy tuning
FEATURE_WEIGHTS = {
    # Tracking and delivery (strong evidence)
    "tracking_available": 0.10,
    "tracking_delivered": 0.15,
    "tracking_matches_address": 0.08,
    "proof_of_delivery": 0.12,
    "signature_on_delivery": 0.10,
    
    # Communication and documentation
    "seller_communication_exists": 0.05,
    "seller_communication_professional": 0.03,
    "item_description_detailed": 0.04,
    "photos_of_item": 0.06,
    
    # Transaction factors
    "order_value_high": -0.05,  # Higher stakes = more scrutiny
    "order_value_low": 0.02,  # Low value often favors seller
    "transaction_recent": -0.03,  # Less time to build case
    "transaction_old": 0.04,  # More established history
    
    # Evidence completeness
    "evidence_complete": 0.08,
    "evidence_partial": 0.00,
    "evidence_minimal": -0.10,
}


def calculate_heuristic_probability(
    dispute: Dispute,
    min_prob: float = 0.02,
    max_prob: float = 0.97
) -> float:
    """
    Calculate win probability using transparent heuristics.
    
    This function starts from a base rate for the dispute reason type,
    then adjusts based on available evidence and dispute characteristics.
    All weights are clearly documented for explainability.
    
    Args:
        dispute: The dispute to score
        min_prob: Minimum clamp value (default 0.02)
        max_prob: Maximum clamp value (default 0.97)
        
    Returns:
        Win probability between min_prob and max_prob
    """
    # Start with base rate for dispute reason
    base_rate = BASE_RATES.get(dispute.reason, 0.35)
    score = base_rate
    
    # Extract evidence features
    evidence_types = set()
    tracking_info = None
    proof_of_delivery = None
    buyer_communication = None
    item_description = None
    photos = None
    
    for item in dispute.evidence_items:
        ev_type = item.get("type", "")
        evidence_types.add(ev_type)
        
        if ev_type == "TRACKING_INFO":
            tracking_info = item
        elif ev_type == "PROOF_OF_DELIVERY":
            proof_of_delivery = item
        elif ev_type == "BUYER_COMMUNICATION":
            buyer_communication = item
        elif ev_type == "ITEM_DESCRIPTION":
            item_description = item
        elif ev_type == "PHOTOS":
            photos = item
    
    # Apply tracking adjustments
    if tracking_info:
        score += FEATURE_WEIGHTS["tracking_available"]
        
        data = tracking_info.get("data", {})
        status = data.get("status", "").lower()
        
        if "delivered" in status:
            score += FEATURE_WEIGHTS["tracking_delivered"]
        
        # Check if tracking matches shipping address (if field exists)
        if data.get("matches_address"):
            score += FEATURE_WEIGHTS["tracking_matches_address"]
    
    # Apply proof of delivery adjustments
    if proof_of_delivery:
        score += FEATURE_WEIGHTS["proof_of_delivery"]
        
        data = proof_of_delivery.get("data", {})
        if data.get("signature"):
            score += FEATURE_WEIGHTS["signature_on_delivery"]
    
    # Apply communication adjustments
    if buyer_communication:
        score += FEATURE_WEIGHTS["seller_communication_exists"]
        
        data = buyer_communication.get("data", {})
        tone = data.get("tone", "").lower()
        
        if tone in ["professional", "friendly", "neutral"]:
            score += FEATURE_WEIGHTS["seller_communication_professional"]
    
    # Apply documentation adjustments
    if item_description:
        score += FEATURE_WEIGHTS["item_description_detailed"]
    
    if photos:
        score += FEATURE_WEIGHTS["photos_of_item"]
    
    # Apply transaction value adjustments
    amount = float(dispute.amount)
    
    if amount > 200:
        score += FEATURE_WEIGHTS["order_value_high"]
    elif amount < 30:
        score += FEATURE_WEIGHTS["order_value_low"]
    
    # Apply transaction age adjustments
    if dispute.created_at:
        from datetime import datetime, UTC
        now = datetime.now(UTC).replace(tzinfo=None)
        days_old = (now - dispute.created_at).days
        
        if days_old < 7:
            score += FEATURE_WEIGHTS["transaction_recent"]
        elif days_old > 30:
            score += FEATURE_WEIGHTS["transaction_old"]
    
    # Apply evidence completeness adjustments
    evidence_count = len(dispute.evidence_items)
    
    if evidence_count >= 4:
        score += FEATURE_WEIGHTS["evidence_complete"]
    elif evidence_count >= 2:
        score += FEATURE_WEIGHTS["evidence_partial"]
    else:
        score += FEATURE_WEIGHTS["evidence_minimal"]
    
    # Clamp to valid range
    score = max(min_prob, min(max_prob, score))
    
    return score


def blend_probabilities(
    heuristic_prob: float,
    llm_prob: float,
    heuristic_weight: float = 0.6,
    llm_weight: float = 0.4
) -> float:
    """
    Blend heuristic and LLM probabilities.
    
    Args:
        heuristic_prob: Probability from heuristic scorer
        llm_prob: Probability from LLM
        heuristic_weight: Weight for heuristic (default 0.6)
        llm_weight: Weight for LLM (default 0.4)
        
    Returns:
        Blended probability
    """
    # Normalize weights
    total_weight = heuristic_weight + llm_weight
    if total_weight == 0:
        return 0.5  # Fallback
    
    h_normalized = heuristic_weight / total_weight
    l_normalized = llm_weight / total_weight
    
    blended = h_normalized * heuristic_prob + l_normalized * llm_prob
    
    return blended


def explain_heuristic_score(dispute: Dispute) -> dict:
    """
    Generate a detailed explanation of heuristic scoring.
    
    Args:
        dispute: The dispute to explain
        
    Returns:
        Dictionary with explanation details
    """
    base_rate = BASE_RATES.get(dispute.reason, 0.35)
    
    factors = {
        "base_rate": {
            "reason": dispute.reason.value,
            "rate": base_rate,
            "note": "Starting probability based on dispute type"
        },
        "adjustments": []
    }
    
    # Track evidence
    evidence_types = {item.get("type", "") for item in dispute.evidence_items}
    
    if "TRACKING_INFO" in evidence_types:
        factors["adjustments"].append({
            "factor": "Tracking information provided",
            "adjustment": FEATURE_WEIGHTS["tracking_available"],
            "impact": "positive"
        })
    
    if "PROOF_OF_DELIVERY" in evidence_types:
        factors["adjustments"].append({
            "factor": "Proof of delivery provided",
            "adjustment": FEATURE_WEIGHTS["proof_of_delivery"],
            "impact": "positive"
        })
    
    # Evidence completeness
    evidence_count = len(dispute.evidence_items)
    if evidence_count >= 4:
        factors["adjustments"].append({
            "factor": "Complete evidence package",
            "adjustment": FEATURE_WEIGHTS["evidence_complete"],
            "impact": "positive"
        })
    elif evidence_count < 2:
        factors["adjustments"].append({
            "factor": "Minimal evidence",
            "adjustment": FEATURE_WEIGHTS["evidence_minimal"],
            "impact": "negative"
        })
    
    # Order value
    amount = float(dispute.amount)
    if amount > 200:
        factors["adjustments"].append({
            "factor": "High order value (>$200)",
            "adjustment": FEATURE_WEIGHTS["order_value_high"],
            "impact": "negative"
        })
    elif amount < 30:
        factors["adjustments"].append({
            "factor": "Low order value (<$30)",
            "adjustment": FEATURE_WEIGHTS["order_value_low"],
            "impact": "positive"
        })
    
    final_score = calculate_heuristic_probability(dispute)
    factors["final_score"] = final_score
    
    return factors
