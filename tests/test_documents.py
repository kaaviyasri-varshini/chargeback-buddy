"""Tests for MongoDB document models."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.db.documents import (
    AgentAnalysis,
    AgentDecision,
    AuditLog,
    Dispute,
    DisputeEvent,
    DisputeReason,
    DisputeStatus,
)


@pytest.mark.asyncio
async def test_create_dispute(test_db):
    """Test creating a dispute document."""
    dispute = Dispute(
        paypal_dispute_id="PP-D-TEST-001",
        buyer_name="Test Buyer",
        buyer_email="test@example.com",
        amount=Decimal("99.99"),
        currency="USD",
        reason=DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED,
        status=DisputeStatus.OPEN,
        due_by=datetime.utcnow() + timedelta(days=7),
        transaction_id="TXN-123",
        order_id="ORD-456",
    )
    
    await dispute.insert()
    
    # Verify it was saved
    found = await Dispute.find_one(Dispute.paypal_dispute_id == "PP-D-TEST-001")
    assert found is not None
    assert found.buyer_name == "Test Buyer"
    assert found.amount == Decimal("99.99")
    assert found.status == DisputeStatus.OPEN


@pytest.mark.asyncio
async def test_dispute_unique_paypal_id(test_db):
    """Test that paypal_dispute_id is unique."""
    dispute1 = Dispute(
        paypal_dispute_id="PP-D-UNIQUE-001",
        buyer_name="Buyer 1",
        buyer_email="buyer1@example.com",
        amount=Decimal("50.00"),
        reason=DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED,
        status=DisputeStatus.OPEN,
    )
    await dispute1.insert()
    
    # Try to insert duplicate
    dispute2 = Dispute(
        paypal_dispute_id="PP-D-UNIQUE-001",  # Same ID
        buyer_name="Buyer 2",
        buyer_email="buyer2@example.com",
        amount=Decimal("75.00"),
        reason=DisputeReason.UNAUTHORISED,
        status=DisputeStatus.OPEN,
    )
    
    with pytest.raises(Exception):  # Should raise duplicate key error
        await dispute2.insert()


@pytest.mark.asyncio
async def test_create_agent_analysis(test_db):
    """Test creating an agent analysis document."""
    # Create a dispute first
    dispute = Dispute(
        paypal_dispute_id="PP-D-TEST-002",
        buyer_name="Test Buyer",
        buyer_email="test@example.com",
        amount=Decimal("100.00"),
        reason=DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED,
        status=DisputeStatus.OPEN,
    )
    await dispute.insert()
    
    # Create analysis
    analysis = AgentAnalysis(
        dispute_id=str(dispute.id),
        decision=AgentDecision.FIGHT,
        confidence=0.85,
        win_probability=0.80,
        refund_loss=Decimal("100.00"),
        fight_expected_loss=Decimal("45.00"),
        fighting_cost=Decimal("25.00"),
        drafted_response="We have strong evidence for this case.",
        reasoning_steps=["Step 1", "Step 2"],
        risks=["Risk 1"],
    )
    
    await analysis.insert()
    
    # Verify
    found = await AgentAnalysis.find_one(AgentAnalysis.dispute_id == str(dispute.id))
    assert found is not None
    assert found.decision == AgentDecision.FIGHT
    assert found.win_probability == 0.80


@pytest.mark.asyncio
async def test_create_dispute_event(test_db):
    """Test creating a dispute event document."""
    event = DisputeEvent(
        event_id="evt_test_001",
        dispute_id="dispute_123",
        event_type="CUSTOMER.DISPUTE.CREATED",
        payload={"test": "data"},
    )
    
    await event.insert()
    
    # Verify
    found = await DisputeEvent.find_one(DisputeEvent.event_id == "evt_test_001")
    assert found is not None
    assert found.event_type == "CUSTOMER.DISPUTE.CREATED"
    assert found.processed is False


@pytest.mark.asyncio
async def test_create_audit_log(test_db):
    """Test creating an audit log entry."""
    audit = AuditLog(
        action="agent_analysis_completed",
        dispute_id="dispute_123",
        actor="agent",
        reasoning="AI completed analysis",
        metadata={"confidence": 0.9},
    )
    
    await audit.insert()
    
    # Verify
    found = await AuditLog.find_one(AuditLog.dispute_id == "dispute_123")
    assert found is not None
    assert found.action == "agent_analysis_completed"
    assert found.actor == "agent"


@pytest.mark.asyncio
async def test_dispute_indexes(test_db):
    """Test that we can query disputes efficiently by indexed fields."""
    # Create multiple disputes
    for i in range(5):
        dispute = Dispute(
            paypal_dispute_id=f"PP-D-INDEX-{i}",
            buyer_name=f"Buyer {i}",
            buyer_email=f"buyer{i}@example.com",
            amount=Decimal(f"{10 + i}.00"),
            reason=DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED,
            status=DisputeStatus.OPEN if i < 3 else DisputeStatus.RESOLVED,
            created_at=datetime.utcnow() - timedelta(days=i),
        )
        await dispute.insert()
    
    # Query by status (indexed)
    open_disputes = await Dispute.find(Dispute.status == DisputeStatus.OPEN).to_list()
    assert len(open_disputes) == 3
    
    # Query by created_at (indexed)
    recent = await Dispute.find(
        Dispute.created_at >= datetime.utcnow() - timedelta(days=2)
    ).to_list()
    assert len(recent) >= 2
