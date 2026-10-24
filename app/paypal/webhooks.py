"""PayPal webhook handlers."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException
from decimal import Decimal

from app.config import settings
from app.db.documents import (
    Dispute,
    DisputeEvent,
    DisputeStatus,
    DisputeReason,
    AuditLog
)
from app.paypal.client import PayPalClient
from app.agent import analyze_dispute

logger = logging.getLogger(__name__)


def create_webhook_router() -> APIRouter:
    """
    Create FastAPI router for PayPal webhooks.
    
    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/api/webhooks/paypal", tags=["webhooks"])
    
    @router.post("/")
    async def handle_webhook(request: Request):
        """
        Handle PayPal webhook events.
        
        Processes CUSTOMER.DISPUTE.CREATED and CUSTOMER.DISPUTE.UPDATED events.
        Verifies webhook signature and processes idempotently by event ID.
        """
        # Get raw body for signature verification
        body = await request.body()
        
        # Parse JSON
        try:
            event_data = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        event_id = event_data.get("id")
        event_type = event_data.get("event_type")
        
        if not event_id or not event_type:
            logger.error("Missing event_id or event_type")
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        logger.info(f"Received webhook: {event_type} (ID: {event_id})")
        
        # Check if we've already processed this event (idempotency)
        existing_event = await DisputeEvent.find_one(DisputeEvent.event_id == event_id)
        if existing_event and existing_event.processed:
            logger.info(f"Event {event_id} already processed, skipping")
            return {"status": "already_processed"}
        
        # Verify webhook signature
        if settings.paypal_webhook_id:
            async with PayPalClient() as client:
                headers = dict(request.headers)
                is_valid = await client.verify_webhook_signature(
                    settings.paypal_webhook_id,
                    headers,
                    body
                )
                
                if not is_valid:
                    logger.warning(f"Invalid webhook signature for event {event_id}")
                    raise HTTPException(status_code=401, detail="Invalid signature")
        else:
            logger.warning("Webhook signature verification skipped (no webhook_id configured)")
        
        # Process the event
        try:
            if event_type == "CUSTOMER.DISPUTE.CREATED":
                await handle_dispute_created(event_id, event_data)
            elif event_type == "CUSTOMER.DISPUTE.UPDATED":
                await handle_dispute_updated(event_id, event_data)
            else:
                logger.info(f"Ignoring event type: {event_type}")
                # Still log it as processed
                if not existing_event:
                    event = DisputeEvent(
                        event_id=event_id,
                        dispute_id="",
                        event_type=event_type,
                        payload=event_data,
                        processed=True
                    )
                    await event.insert()
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Error processing webhook event {event_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal error")
    
    return router


async def handle_dispute_created(event_id: str, event_data: Dict[str, Any]):
    """
    Handle CUSTOMER.DISPUTE.CREATED event.
    
    Args:
        event_id: Webhook event ID
        event_data: Event payload
    """
    resource = event_data.get("resource", {})
    dispute_id = resource.get("dispute_id")
    
    if not dispute_id:
        logger.error("Missing dispute_id in DISPUTE.CREATED event")
        return
    
    logger.info(f"Processing new dispute: {dispute_id}")
    
    # Check if dispute already exists
    existing = await Dispute.find_one(Dispute.paypal_dispute_id == dispute_id)
    if existing:
        logger.info(f"Dispute {dispute_id} already exists, updating")
        dispute = existing
    else:
        # Create new dispute from webhook data
        dispute = Dispute(
            paypal_dispute_id=dispute_id,
            buyer_name=resource.get("buyer_name", "Unknown"),
            buyer_email=resource.get("buyer_email", ""),
            amount=Decimal(str(resource.get("dispute_amount", {}).get("value", "0"))),
            currency=resource.get("dispute_amount", {}).get("currency_code", "USD"),
            reason=_parse_dispute_reason(resource.get("reason")),
            status=_parse_dispute_status(resource.get("status")),
            transaction_id=resource.get("transactions", [{}])[0].get("transaction_id"),
            order_id=resource.get("transactions", [{}])[0].get("custom"),
            evidence_items=[]
        )
        await dispute.insert()
        logger.info(f"Created dispute {dispute_id}")
    
    # Create event record
    event = DisputeEvent(
        event_id=event_id,
        dispute_id=str(dispute.id),
        event_type="CUSTOMER.DISPUTE.CREATED",
        payload=event_data,
        processed=False  # Will be marked processed after agent analysis
    )
    await event.insert()
    
    # Run agent analysis
    logger.info(f"Running agent analysis for dispute {dispute_id}...")
    analysis = await analyze_dispute(dispute, persist=True)
    
    logger.info(f"Agent recommendation for {dispute_id}: {analysis.decision.value}")
    
    # Mark event as processed
    event.processed = True
    await event.save()
    
    # Create audit log
    audit = AuditLog(
        action="webhook_dispute_created",
        dispute_id=str(dispute.id),
        actor="paypal_webhook",
        reasoning=f"New dispute received from PayPal. Agent analyzed and recommended: {analysis.decision.value}",
        metadata={
            "event_id": event_id,
            "webhook_type": "CUSTOMER.DISPUTE.CREATED"
        }
    )
    await audit.insert()


async def handle_dispute_updated(event_id: str, event_data: Dict[str, Any]):
    """
    Handle CUSTOMER.DISPUTE.UPDATED event.
    
    Args:
        event_id: Webhook event ID
        event_data: Event payload
    """
    resource = event_data.get("resource", {})
    dispute_id = resource.get("dispute_id")
    
    if not dispute_id:
        logger.error("Missing dispute_id in DISPUTE.UPDATED event")
        return
    
    logger.info(f"Processing dispute update: {dispute_id}")
    
    # Find existing dispute
    dispute = await Dispute.find_one(Dispute.paypal_dispute_id == dispute_id)
    if not dispute:
        logger.warning(f"Dispute {dispute_id} not found, cannot update")
        # Create it if missing
        await handle_dispute_created(event_id, event_data)
        return
    
    # Update dispute fields
    old_status = dispute.status
    dispute.status = _parse_dispute_status(resource.get("status"))
    dispute.updated_at = datetime.utcnow()
    await dispute.save()
    
    logger.info(f"Updated dispute {dispute_id} status: {old_status.value} -> {dispute.status.value}")
    
    # Create event record
    event = DisputeEvent(
        event_id=event_id,
        dispute_id=str(dispute.id),
        event_type="CUSTOMER.DISPUTE.UPDATED",
        payload=event_data,
        processed=True
    )
    await event.insert()
    
    # Create audit log
    audit = AuditLog(
        action="webhook_dispute_updated",
        dispute_id=str(dispute.id),
        actor="paypal_webhook",
        reasoning=f"Dispute status changed from {old_status.value} to {dispute.status.value}",
        metadata={
            "event_id": event_id,
            "webhook_type": "CUSTOMER.DISPUTE.UPDATED",
            "old_status": old_status.value,
            "new_status": dispute.status.value
        }
    )
    await audit.insert()


def _parse_dispute_reason(reason: Optional[str]) -> DisputeReason:
    """Parse PayPal dispute reason to our enum."""
    if not reason:
        return DisputeReason.OTHER
    
    reason_upper = reason.upper()
    
    # Map PayPal reason codes to our enum
    reason_map = {
        "MERCHANDISE_OR_SERVICE_NOT_RECEIVED": DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED,
        "MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED": DisputeReason.MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED,
        "UNAUTHORISED": DisputeReason.UNAUTHORISED,
        "UNAUTHORIZED": DisputeReason.UNAUTHORISED,
        "CREDIT_NOT_PROCESSED": DisputeReason.CREDIT_NOT_PROCESSED,
        "DUPLICATE_TRANSACTION": DisputeReason.DUPLICATE_TRANSACTION,
        "INCORRECT_AMOUNT": DisputeReason.INCORRECT_AMOUNT,
        "PAYMENT_BY_OTHER_MEANS": DisputeReason.PAYMENT_BY_OTHER_MEANS,
        "CANCELED_RECURRING_BILLING": DisputeReason.CANCELED_RECURRING_BILLING,
        "PROBLEM_WITH_REMITTANCE": DisputeReason.PROBLEM_WITH_REMITTANCE,
    }
    
    return reason_map.get(reason_upper, DisputeReason.OTHER)


def _parse_dispute_status(status: Optional[str]) -> DisputeStatus:
    """Parse PayPal dispute status to our enum."""
    if not status:
        return DisputeStatus.OPEN
    
    status_upper = status.upper()
    
    # Map PayPal status codes to our enum
    status_map = {
        "OPEN": DisputeStatus.OPEN,
        "WAITING_FOR_SELLER_RESPONSE": DisputeStatus.WAITING_FOR_SELLER_RESPONSE,
        "WAITING_FOR_BUYER_RESPONSE": DisputeStatus.WAITING_FOR_BUYER_RESPONSE,
        "UNDER_REVIEW": DisputeStatus.UNDER_REVIEW,
        "RESOLVED": DisputeStatus.RESOLVED,
        "APPEALED": DisputeStatus.APPEALED,
        "CLOSED": DisputeStatus.CLOSED,
    }
    
    return status_map.get(status_upper, DisputeStatus.OPEN)
