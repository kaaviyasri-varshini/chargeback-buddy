"""PayPal sandbox demonstration script.

This script demonstrates the complete PayPal dispute flow:
1. Fetch a dispute from PayPal sandbox
2. Run AI agent analysis
3. Submit evidence if recommended to FIGHT
4. Show the complete flow with detailed output
"""

import asyncio
import argparse
import logging
import json
import sys
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, '/Users/kaaviya/hackathon/chargeback-buddy')

from app.config import settings
from app.db.connection import init_db, close_db
from app.db.documents import Dispute, DisputeReason, DisputeStatus, AgentDecision
from app.paypal.client import PayPalClient
from app.agent import analyze_dispute

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_dispute_flow(dispute_id: str):
    """
    Demonstrate the complete dispute flow.
    
    Args:
        dispute_id: PayPal dispute ID to process
    """
    print("\n" + "="*80)
    print(" PayPal Sandbox Dispute Flow Demo")
    print("="*80 + "\n")
    
    try:
        # Initialize database
        print("📊 Initializing database connection...")
        await init_db()
        print("✅ Database connected\n")
        
        # Step 1: Fetch dispute from PayPal
        print(f"📥 Step 1: Fetching dispute {dispute_id} from PayPal sandbox...")
        async with PayPalClient() as client:
            try:
                paypal_dispute = await client.get_dispute(dispute_id)
                print(f"✅ Successfully fetched dispute")
                print(f"   - Buyer: {paypal_dispute.get('buyer', {}).get('name', 'Unknown')}")
                print(f"   - Amount: {paypal_dispute.get('dispute_amount', {}).get('value')} {paypal_dispute.get('dispute_amount', {}).get('currency_code')}")
                print(f"   - Reason: {paypal_dispute.get('reason', 'Unknown')}")
                print(f"   - Status: {paypal_dispute.get('status', 'Unknown')}")
                print()
            except Exception as e:
                print(f"❌ Failed to fetch dispute from PayPal: {e}")
                print("   This is expected if you don't have valid sandbox credentials.")
                print("   Continuing with mock data...\n")
                paypal_dispute = None
        
        # Step 2: Create/update dispute in database
        print("💾 Step 2: Storing dispute in database...")
        
        if paypal_dispute:
            # Use real data
            dispute = Dispute(
                paypal_dispute_id=dispute_id,
                buyer_name=paypal_dispute.get('buyer', {}).get('name', 'Test Buyer'),
                buyer_email=paypal_dispute.get('buyer', {}).get('email', 'buyer@test.com'),
                amount=Decimal(str(paypal_dispute.get('dispute_amount', {}).get('value', '100.00'))),
                currency=paypal_dispute.get('dispute_amount', {}).get('currency_code', 'USD'),
                reason=_parse_reason(paypal_dispute.get('reason')),
                status=_parse_status(paypal_dispute.get('status')),
                evidence_items=[]
            )
        else:
            # Use mock data for demo
            dispute = Dispute(
                paypal_dispute_id=dispute_id,
                buyer_name="Demo Buyer",
                buyer_email="demo@buyer.com",
                amount=Decimal("150.00"),
                currency="USD",
                reason=DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED,
                status=DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
                evidence_items=[
                    {
                        "type": "TRACKING_INFO",
                        "data": {"carrier": "UPS", "tracking": "1Z999AA10123456784", "status": "Delivered"},
                        "strength_score": 0.92
                    },
                    {
                        "type": "PROOF_OF_DELIVERY",
                        "data": {"signature": "D. Buyer", "date": "2024-01-15"},
                        "strength_score": 0.88
                    },
                    {
                        "type": "BUYER_COMMUNICATION",
                        "data": {"messages": 2, "tone": "neutral"},
                        "strength_score": 0.65
                    }
                ]
            )
        
        await dispute.insert()
        print(f"✅ Dispute stored with ID: {dispute.id}")
        print()
        
        # Step 3: Run AI agent analysis
        print("🤖 Step 3: Running AI agent analysis...")
        print("   This combines heuristic scoring with LLM reasoning...")
        print()
        
        analysis = await analyze_dispute(dispute, persist=True)
        
        print("📊 Analysis Results:")
        print("-" * 60)
        print(f"   Decision: {analysis.decision.value}")
        print(f"   Confidence: {analysis.confidence:.0%}")
        print(f"   ")
        if analysis.heuristic_probability is not None:
            print(f"   Heuristic Win Probability: {analysis.heuristic_probability:.0%}")
        if analysis.llm_probability is not None:
            print(f"   LLM Win Probability: {analysis.llm_probability:.0%}")
        print(f"   Blended Win Probability: {analysis.win_probability:.0%}")
        print(f"   ")
        print(f"   Expected Loss (Fight): ${analysis.fight_expected_loss:.2f}")
        print(f"   Expected Loss (Refund): ${analysis.refund_loss:.2f}")
        print()
        
        print("📝 Reasoning:")
        for step in analysis.reasoning_steps:
            print(f"   • {step}")
        print()
        
        # Step 4: Submit evidence if FIGHT recommended
        if analysis.decision == AgentDecision.FIGHT:
            print("⚔️  Step 4: Submitting evidence to PayPal (FIGHT recommended)...")
            
            async with PayPalClient() as client:
                try:
                    result = await client.provide_evidence(
                        dispute_id,
                        notes=analysis.drafted_response
                    )
                    print(f"✅ Evidence submitted successfully")
                    print(f"   Response: {json.dumps(result, indent=2)}")
                except Exception as e:
                    print(f"❌ Failed to submit evidence: {e}")
                    print("   This is expected without valid sandbox credentials.")
                    print(f"   ")
                    print(f"   Would have submitted:")
                    print(f"   {analysis.drafted_response}")
        else:
            print("🏳️  Step 4: Refund recommended - no evidence submission")
            print(f"   Draft message: {analysis.drafted_response}")
        
        print()
        print("="*80)
        print(" Demo Complete!")
        print("="*80)
        print()
        print("Summary:")
        print(f"  - Dispute: {dispute_id}")
        print(f"  - Amount: ${dispute.amount}")
        print(f"  - Recommendation: {analysis.decision.value}")
        print(f"  - Win Probability: {analysis.win_probability:.0%}")
        print(f"  - Expected Savings: ${max(Decimal('0'), analysis.refund_loss - analysis.fight_expected_loss):.2f}")
        print()
        
    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")
    finally:
        await close_db()


def _parse_reason(reason: str) -> DisputeReason:
    """Parse PayPal reason to enum."""
    if not reason:
        return DisputeReason.OTHER
    
    reason_map = {
        "MERCHANDISE_OR_SERVICE_NOT_RECEIVED": DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED,
        "MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED": DisputeReason.MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED,
        "UNAUTHORISED": DisputeReason.UNAUTHORISED,
    }
    return reason_map.get(reason.upper(), DisputeReason.OTHER)


def _parse_status(status: str) -> DisputeStatus:
    """Parse PayPal status to enum."""
    if not status:
        return DisputeStatus.OPEN
    
    status_map = {
        "OPEN": DisputeStatus.OPEN,
        "WAITING_FOR_SELLER_RESPONSE": DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
        "UNDER_REVIEW": DisputeStatus.UNDER_REVIEW,
        "RESOLVED": DisputeStatus.RESOLVED,
    }
    return status_map.get(status.upper(), DisputeStatus.OPEN)


async def replay_webhook_demo():
    """Replay a saved webhook payload for demo purposes."""
    print("\n" + "="*80)
    print(" Webhook Replay Demo (Fallback)")
    print("="*80 + "\n")
    
    # Sample webhook payload
    webhook_payload = {
        "id": "WH-DEMO-12345",
        "event_type": "CUSTOMER.DISPUTE.CREATED",
        "resource": {
            "dispute_id": "PP-D-DEMO-001",
            "buyer_name": "Demo Buyer",
            "buyer_email": "demo@example.com",
            "dispute_amount": {
                "currency_code": "USD",
                "value": "99.99"
            },
            "reason": "MERCHANDISE_OR_SERVICE_NOT_RECEIVED",
            "status": "OPEN"
        }
    }
    
    print("📧 Simulating webhook event:")
    print(json.dumps(webhook_payload, indent=2))
    print()
    
    # Process it through our demo flow
    await demo_dispute_flow(webhook_payload["resource"]["dispute_id"])


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PayPal Sandbox Demo")
    parser.add_argument(
        "--dispute-id",
        type=str,
        help="PayPal dispute ID to process"
    )
    parser.add_argument(
        "--replay-webhook",
        action="store_true",
        help="Replay a saved webhook payload (fallback if no sandbox access)"
    )
    
    args = parser.parse_args()
    
    if args.replay_webhook or not args.dispute_id:
        # Fallback mode
        asyncio.run(replay_webhook_demo())
    else:
        # Live sandbox mode
        asyncio.run(demo_dispute_flow(args.dispute_id))


if __name__ == "__main__":
    main()
