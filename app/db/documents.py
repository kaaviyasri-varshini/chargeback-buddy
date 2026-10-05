"""Beanie document models for MongoDB collections."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from beanie import Document, Indexed
from pydantic import Field, field_serializer, field_validator
from bson import Decimal128


class DisputeStatus(str, Enum):
    """Dispute status values."""
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    WAITING_FOR_SELLER_RESPONSE = "WAITING_FOR_SELLER_RESPONSE"
    WAITING_FOR_BUYER_RESPONSE = "WAITING_FOR_BUYER_RESPONSE"
    APPEALED = "APPEALED"
    CLOSED = "CLOSED"


class DisputeReason(str, Enum):
    """Dispute reason codes."""
    MERCHANDISE_OR_SERVICE_NOT_RECEIVED = "MERCHANDISE_OR_SERVICE_NOT_RECEIVED"
    MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED = "MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED"
    UNAUTHORISED = "UNAUTHORISED"
    CREDIT_NOT_PROCESSED = "CREDIT_NOT_PROCESSED"
    DUPLICATE_TRANSACTION = "DUPLICATE_TRANSACTION"
    INCORRECT_AMOUNT = "INCORRECT_AMOUNT"
    PAYMENT_BY_OTHER_MEANS = "PAYMENT_BY_OTHER_MEANS"
    CANCELED_RECURRING_BILLING = "CANCELED_RECURRING_BILLING"
    PROBLEM_WITH_REMITTANCE = "PROBLEM_WITH_REMITTANCE"
    OTHER = "OTHER"


class AgentDecision(str, Enum):
    """Agent recommendation decision."""
    FIGHT = "FIGHT"
    REFUND = "REFUND"


class EvidenceItem(Enum):
    """Types of evidence."""
    TRACKING_INFO = "TRACKING_INFO"
    PROOF_OF_DELIVERY = "PROOF_OF_DELIVERY"
    PROOF_OF_REFUND = "PROOF_OF_REFUND"
    ITEM_DESCRIPTION = "ITEM_DESCRIPTION"
    BUYER_COMMUNICATION = "BUYER_COMMUNICATION"
    MERCHANT_NOTES = "MERCHANT_NOTES"
    RETURN_POLICY = "RETURN_POLICY"
    INVOICE = "INVOICE"
    PHOTOS = "PHOTOS"


class EvidenceData(dict):
    """Evidence item with strength score (embedded document)."""
    type: str
    data: dict[str, Any]
    strength_score: float  # 0.0 to 1.0
    notes: str = ""


class Dispute(Document):
    """Main dispute document."""
    
    paypal_dispute_id: Indexed(str, unique=True)  # type: ignore
    buyer_name: str
    buyer_email: str
    amount: Decimal
    currency: str = "USD"
    reason: DisputeReason
    status: DisputeStatus
    due_by: Optional[datetime] = None
    created_at: Indexed(datetime) = Field(default_factory=datetime.utcnow)  # type: ignore
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Transaction details
    transaction_id: Optional[str] = None
    order_id: Optional[str] = None
    
    # Evidence (embedded)
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)
    
    # Latest analysis reference
    latest_analysis_id: Optional[str] = None
    
    # Seller response
    seller_response_submitted: bool = False
    seller_response_submitted_at: Optional[datetime] = None
    
    class Settings:
        name = "disputes"
        indexes = [
            "status",
            "created_at",
            [("status", 1), ("due_by", 1)],
        ]
        bson_encoders = {
            Decimal: lambda v: Decimal128(str(v))
        }
    
    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v):
        """Convert Decimal128 to Decimal."""
        if isinstance(v, Decimal128):
            return Decimal(str(v))
        return v
    
    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        """Serialize Decimal to string for JSON."""
        return str(value)


class DisputeEvent(Document):
    """Webhook events and timeline entries for disputes."""
    
    event_id: Indexed(str, unique=True)  # type: ignore
    dispute_id: str
    event_type: str
    payload: dict[str, Any]
    received_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    
    class Settings:
        name = "dispute_events"
        indexes = [
            "dispute_id",
            "received_at",
            [("dispute_id", 1), ("received_at", -1)],
        ]


class AgentAnalysis(Document):
    """AI agent analysis and recommendation for a dispute."""
    
    dispute_id: str
    decision: AgentDecision
    confidence: float  # 0.0 to 1.0
    win_probability: float  # 0.0 to 1.0
    
    # Expected value calculations
    refund_loss: Decimal
    fight_expected_loss: Decimal
    fighting_cost: Decimal
    
    # Evidence assessment (embedded)
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)
    
    # Generated response
    drafted_response: str
    response_tone: str = "professional"  # professional, friendly, firm
    
    # Reasoning
    reasoning_steps: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "agent_analyses"
        indexes = [
            "dispute_id",
            "created_at",
            [("dispute_id", 1), ("created_at", -1)],
        ]
        bson_encoders = {
            Decimal: lambda v: Decimal128(str(v))
        }
    
    @field_validator("refund_loss", "fight_expected_loss", "fighting_cost", mode="before")
    @classmethod
    def validate_decimal(cls, v):
        """Convert Decimal128 to Decimal."""
        if isinstance(v, Decimal128):
            return Decimal(str(v))
        return v
    
    @field_serializer("refund_loss", "fight_expected_loss", "fighting_cost")
    def serialize_decimal(self, value: Decimal) -> str:
        """Serialize Decimal to string for JSON."""
        return str(value)


class AuditLog(Document):
    """Audit log for all agent actions and human decisions."""
    
    action: str  # "agent_analysis", "human_approved_fight", "human_approved_refund", etc.
    dispute_id: str
    actor: str  # "agent" or username
    reasoning: str
    approver: Optional[str] = None
    
    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "audit_logs"
        indexes = [
            "dispute_id",
            "timestamp",
            [("dispute_id", 1), ("timestamp", -1)],
        ]


# Initialize document list for Beanie
ALL_DOCUMENTS = [
    Dispute,
    DisputeEvent,
    AgentAnalysis,
    AuditLog,
]
