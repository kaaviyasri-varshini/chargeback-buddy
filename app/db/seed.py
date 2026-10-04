"""Seed the database with realistic mock disputes for demo purposes."""

import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from random import choice, randint, random, shuffle

from app.config import settings
from app.db.connection import init_db, close_db
from app.db.documents import (
    AgentAnalysis,
    AgentDecision,
    AuditLog,
    Dispute,
    DisputeEvent,
    DisputeReason,
    DisputeStatus,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Realistic buyer names
BUYER_NAMES = [
    "Sarah Johnson", "Michael Chen", "Emily Rodriguez", "James Smith",
    "Jessica Williams", "David Brown", "Amanda Davis", "Robert Taylor",
    "Jennifer Martinez", "Christopher Wilson", "Lisa Anderson", "Daniel Thomas",
    "Karen Jackson", "Matthew White", "Nancy Harris", "Kevin Martin",
    "Betty Thompson", "Paul Garcia", "Sandra Martinez", "Mark Robinson"
]

# Product names
PRODUCTS = [
    "Wireless Bluetooth Headphones",
    "Leather Wallet",
    "Smartphone Case",
    "Vintage T-Shirt",
    "Running Shoes",
    "Coffee Maker",
    "Yoga Mat",
    "Backpack",
    "Sunglasses",
    "Watch Band",
    "Phone Charger",
    "Laptop Sleeve",
    "Water Bottle",
    "Desk Lamp",
    "Portable Speaker"
]


async def seed_disputes(reset: bool = False) -> None:
    """
    Seed the database with realistic dispute data.
    
    Args:
        reset: If True, drop existing data first
    """
    logger.info("Starting database seed...")
    
    if reset:
        logger.info("Resetting database...")
        await Dispute.delete_all()
        await DisputeEvent.delete_all()
        await AgentAnalysis.delete_all()
        await AuditLog.delete_all()
        logger.info("Existing data cleared")
    
    # Check if already seeded
    existing_count = await Dispute.count()
    if existing_count > 0 and not reset:
        logger.info(f"Database already contains {existing_count} disputes. Use --reset to clear.")
        return
    
    now = datetime.utcnow()
    disputes_data = []
    
    # Scenario 1: Strong case - Item not received with solid tracking (FIGHT recommended)
    disputes_data.append({
        "paypal_dispute_id": "PP-D-2024-001",
        "buyer_name": "Sarah Johnson",
        "buyer_email": "sarah.j@email.com",
        "amount": Decimal("89.99"),
        "reason": DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED,
        "status": DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
        "due_by": now + timedelta(days=5),
        "created_at": now - timedelta(days=2),
        "order_id": "ORD-2024-12345",
        "transaction_id": "TXN-789456123",
        "evidence_items": [
            {"type": "TRACKING_INFO", "data": {"carrier": "UPS", "tracking": "1Z999AA10123456784", "status": "Delivered"}, "strength_score": 0.95},
            {"type": "PROOF_OF_DELIVERY", "data": {"signature": "S. Johnson", "photo": "signature.jpg"}, "strength_score": 0.98},
            {"type": "BUYER_COMMUNICATION", "data": {"messages": 3, "tone": "neutral"}, "strength_score": 0.6},
        ],
        "decision": AgentDecision.FIGHT,
        "confidence": 0.92,
        "win_probability": 0.88,
    })
    
    # Scenario 2: Weak case - Item not as described with buyer photos (REFUND recommended)
    disputes_data.append({
        "paypal_dispute_id": "PP-D-2024-002",
        "buyer_name": "Michael Chen",
        "buyer_email": "m.chen@email.com",
        "amount": Decimal("45.50"),
        "reason": DisputeReason.MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED,
        "status": DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
        "due_by": now + timedelta(days=3),
        "created_at": now - timedelta(days=4),
        "order_id": "ORD-2024-12346",
        "transaction_id": "TXN-789456124",
        "evidence_items": [
            {"type": "ITEM_DESCRIPTION", "data": {"listing_text": "Vintage style t-shirt"}, "strength_score": 0.4},
            {"type": "PHOTOS", "data": {"buyer_photos": 3, "shows_damage": True}, "strength_score": 0.7},
            {"type": "BUYER_COMMUNICATION", "data": {"messages": 5, "tone": "upset"}, "strength_score": 0.3},
        ],
        "decision": AgentDecision.REFUND,
        "confidence": 0.78,
        "win_probability": 0.25,
    })
    
    # Scenario 3: Low value dispute - cheaper to refund (REFUND recommended)
    disputes_data.append({
        "paypal_dispute_id": "PP-D-2024-003",
        "buyer_name": "Emily Rodriguez",
        "buyer_email": "emily.r@email.com",
        "amount": Decimal("12.99"),
        "reason": DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED,
        "status": DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
        "due_by": now + timedelta(days=7),
        "created_at": now - timedelta(hours=18),
        "order_id": "ORD-2024-12347",
        "transaction_id": "TXN-789456125",
        "evidence_items": [
            {"type": "TRACKING_INFO", "data": {"carrier": "USPS", "tracking": "9400111899562838472451", "status": "In Transit"}, "strength_score": 0.5},
        ],
        "decision": AgentDecision.REFUND,
        "confidence": 0.85,
        "win_probability": 0.60,
    })
    
    # Scenario 4: Unauthorized transaction (REFUND recommended)
    disputes_data.append({
        "paypal_dispute_id": "PP-D-2024-004",
        "buyer_name": "James Smith",
        "buyer_email": "j.smith@email.com",
        "amount": Decimal("156.00"),
        "reason": DisputeReason.UNAUTHORISED,
        "status": DisputeStatus.UNDER_REVIEW,
        "due_by": now + timedelta(days=2),
        "created_at": now - timedelta(days=6),
        "order_id": "ORD-2024-12348",
        "transaction_id": "TXN-789456126",
        "evidence_items": [
            {"type": "MERCHANT_NOTES", "data": {"note": "Buyer claims account was hacked"}, "strength_score": 0.2},
        ],
        "decision": AgentDecision.REFUND,
        "confidence": 0.95,
        "win_probability": 0.05,
        "seller_response_submitted": True,
        "seller_response_submitted_at": now - timedelta(days=1),
    })
    
    # Generate 16 more random disputes
    for i in range(5, 21):
        shuffle(BUYER_NAMES)
        buyer_name = BUYER_NAMES[0]
        buyer_email = buyer_name.lower().replace(" ", ".") + "@email.com"
        
        amount = Decimal(str(round(random() * 200 + 10, 2)))
        reason = choice(list(DisputeReason))
        
        # Vary the status
        if i < 15:
            status = DisputeStatus.WAITING_FOR_SELLER_RESPONSE
        elif i < 18:
            status = DisputeStatus.UNDER_REVIEW
        else:
            status = DisputeStatus.RESOLVED
        
        days_ago = randint(1, 14)
        days_until_due = randint(1, 10) if status == DisputeStatus.WAITING_FOR_SELLER_RESPONSE else 0
        
        # Random evidence
        num_evidence = randint(1, 4)
        evidence_items = []
        for _ in range(num_evidence):
            ev_type = choice(["TRACKING_INFO", "PROOF_OF_DELIVERY", "BUYER_COMMUNICATION", "ITEM_DESCRIPTION"])
            strength = round(random(), 2)
            evidence_items.append({
                "type": ev_type,
                "data": {"info": "Sample evidence data"},
                "strength_score": strength,
            })
        
        # Calculate win probability based on evidence
        avg_strength = sum(e["strength_score"] for e in evidence_items) / len(evidence_items) if evidence_items else 0.5
        win_prob = round(avg_strength * 0.9 + random() * 0.1, 2)
        
        # Decision logic
        fighting_cost = float(settings.fighting_cost)
        refund_loss = float(amount)
        fight_expected_loss = (1 - win_prob) * float(amount) + fighting_cost
        
        if win_prob * float(amount) > fighting_cost + float(settings.risk_buffer):
            decision = AgentDecision.FIGHT
            confidence = round(0.7 + random() * 0.25, 2)
        else:
            decision = AgentDecision.REFUND
            confidence = round(0.75 + random() * 0.2, 2)
        
        disputes_data.append({
            "paypal_dispute_id": f"PP-D-2024-{str(i).zfill(3)}",
            "buyer_name": buyer_name,
            "buyer_email": buyer_email,
            "amount": amount,
            "reason": reason,
            "status": status,
            "due_by": now + timedelta(days=days_until_due) if days_until_due > 0 else None,
            "created_at": now - timedelta(days=days_ago),
            "order_id": f"ORD-2024-{12344 + i}",
            "transaction_id": f"TXN-{789456122 + i}",
            "evidence_items": evidence_items,
            "decision": decision,
            "confidence": confidence,
            "win_probability": win_prob,
            "seller_response_submitted": status != DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
            "seller_response_submitted_at": now - timedelta(days=randint(1, days_ago)) if status != DisputeStatus.WAITING_FOR_SELLER_RESPONSE else None,
        })
    
    # Insert disputes and related data
    logger.info(f"Inserting {len(disputes_data)} disputes...")
    
    for data in disputes_data:
        # Extract analysis fields
        decision = data.pop("decision")
        confidence = data.pop("confidence")
        win_probability = data.pop("win_probability")
        evidence_items = data["evidence_items"]
        
        # Create dispute
        dispute = Dispute(**data)
        await dispute.insert()
        
        # Create initial event
        event = DisputeEvent(
            event_id=f"evt_{dispute.paypal_dispute_id}_created",
            dispute_id=str(dispute.id),
            event_type="CUSTOMER.DISPUTE.CREATED",
            payload={
                "dispute_id": dispute.paypal_dispute_id,
                "reason": dispute.reason.value,
                "amount": str(dispute.amount),
            },
            processed=True,
        )
        await event.insert()
        
        # Create agent analysis
        fighting_cost = settings.fighting_cost
        refund_loss = dispute.amount
        fight_expected_loss = Decimal(str((1 - win_probability))) * dispute.amount + fighting_cost
        
        reasoning_steps = [
            f"Analyzed {len(evidence_items)} pieces of evidence",
            f"Average evidence strength: {sum(e['strength_score'] for e in evidence_items) / len(evidence_items):.2f}",
            f"Win probability estimated at {win_probability:.0%}",
            f"Expected loss if we fight: ${fight_expected_loss:.2f}",
            f"Expected loss if we refund: ${refund_loss:.2f}",
        ]
        
        if decision == AgentDecision.FIGHT:
            reasoning_steps.append(f"Fighting has better expected value ({win_probability * float(dispute.amount) - float(fighting_cost):.2f} > -{float(refund_loss):.2f})")
            drafted_response = f"We have strong evidence showing the item was delivered to the buyer's address with signature confirmation. Our records show the tracking number confirms delivery on [date]. We request this dispute be resolved in the seller's favor."
        else:
            reasoning_steps.append("Refunding is the better financial decision given the evidence and costs")
            drafted_response = f"We understand the buyer's concern and want to ensure customer satisfaction. We are willing to process a full refund of ${dispute.amount} to resolve this matter amicably."
        
        analysis = AgentAnalysis(
            dispute_id=str(dispute.id),
            decision=decision,
            confidence=confidence,
            win_probability=win_probability,
            refund_loss=refund_loss,
            fight_expected_loss=fight_expected_loss,
            fighting_cost=fighting_cost,
            evidence_items=evidence_items,
            drafted_response=drafted_response,
            reasoning_steps=reasoning_steps,
            risks=["Buyer may escalate to credit card chargeback", "Could impact seller metrics"] if decision == AgentDecision.FIGHT else ["Lost revenue from refund"],
        )
        await analysis.insert()
        
        # Update dispute with analysis reference
        dispute.latest_analysis_id = str(analysis.id)
        await dispute.save()
        
        # Create audit log
        audit = AuditLog(
            action="agent_analysis_completed",
            dispute_id=str(dispute.id),
            actor="agent",
            reasoning=f"AI agent analyzed dispute and recommended: {decision.value}",
            metadata={
                "confidence": confidence,
                "win_probability": win_probability,
                "decision": decision.value,
            },
        )
        await audit.insert()
        
        # If already submitted, add human approval audit
        if dispute.seller_response_submitted:
            approval_audit = AuditLog(
                action=f"human_approved_{decision.value.lower()}",
                dispute_id=str(dispute.id),
                actor="human",
                approver="demo_user",
                reasoning=f"Approved agent recommendation to {decision.value.lower()}",
                timestamp=dispute.seller_response_submitted_at or dispute.updated_at,
            )
            await approval_audit.insert()
    
    logger.info(f"✅ Successfully seeded {len(disputes_data)} disputes with analyses and audit logs")
    
    # Print summary
    fight_count = sum(1 for d in disputes_data if d.get("seller_response_submitted") and any("FIGHT" in str(v) for v in d.values()))
    refund_count = sum(1 for d in disputes_data if d.get("seller_response_submitted") and any("REFUND" in str(v) for v in d.values()))
    
    logger.info(f"Summary:")
    logger.info(f"  - Total disputes: {len(disputes_data)}")
    logger.info(f"  - Waiting for response: {sum(1 for d in disputes_data if d['status'] == DisputeStatus.WAITING_FOR_SELLER_RESPONSE)}")
    logger.info(f"  - Under review: {sum(1 for d in disputes_data if d['status'] == DisputeStatus.UNDER_REVIEW)}")
    logger.info(f"  - Resolved: {sum(1 for d in disputes_data if d['status'] == DisputeStatus.RESOLVED)}")


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Seed ChargeBack Buddy database")
    parser.add_argument("--reset", action="store_true", help="Drop existing data before seeding")
    args = parser.parse_args()
    
    try:
        await init_db()
        await seed_disputes(reset=args.reset)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
