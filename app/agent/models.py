"""Pydantic models for agent structured output."""

from enum import Enum
from pydantic import BaseModel, Field, field_validator


class EvidenceWeight(str, Enum):
    """Weight of evidence impact."""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class EvidenceFor(BaseModel):
    """Evidence that helps the seller."""
    item: str = Field(..., description="What evidence exists")
    why_it_helps: str = Field(..., description="Why this helps the seller's case")
    weight: EvidenceWeight = Field(..., description="How impactful this evidence is")


class EvidenceAgainst(BaseModel):
    """Evidence that hurts the seller."""
    item: str = Field(..., description="What evidence or gap exists")
    why_it_hurts: str = Field(..., description="Why this hurts the seller's case")
    weight: EvidenceWeight = Field(..., description="How impactful this is")


class ConfidenceLevel(str, Enum):
    """Confidence in the analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StructuredDisputeAnalysis(BaseModel):
    """Structured analysis output from Gemini."""
    
    evidence_for: list[EvidenceFor] = Field(
        default_factory=list,
        description="Evidence supporting the seller"
    )
    
    evidence_against: list[EvidenceAgainst] = Field(
        default_factory=list,
        description="Evidence against the seller or gaps"
    )
    
    missing_evidence: list[str] = Field(
        default_factory=list,
        description="What additional evidence the seller should gather"
    )
    
    llm_win_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability that seller will win the dispute"
    )
    
    confidence: ConfidenceLevel = Field(
        ...,
        description="Confidence level in this analysis"
    )
    
    reasoning_summary: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Plain English summary for non-technical seller (2-3 sentences)"
    )
    
    @field_validator("reasoning_summary")
    @classmethod
    def validate_reasoning_length(cls, v: str) -> str:
        """Ensure reasoning is concise but informative."""
        sentences = v.split(". ")
        if len(sentences) < 2:
            raise ValueError("Reasoning summary must contain at least 2 sentences")
        return v
