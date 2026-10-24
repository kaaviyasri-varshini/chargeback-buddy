"""Gemini-powered dispute analyzer with structured output."""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from pydantic import ValidationError

from app.config import settings
from app.db.documents import Dispute, AgentAnalysis, AgentDecision, AuditLog
from app.agent.models import StructuredDisputeAnalysis, ConfidenceLevel
from app.agent.scoring import calculate_heuristic_probability, blend_probabilities

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """Gemini-powered dispute analyzer with structured output."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize the Gemini analyzer.
        
        Args:
            api_key: Gemini API key (defaults to settings)
            model_name: Model name (defaults to settings)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.ai_model
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize model with safety settings
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
    
    def _build_analysis_prompt(self, dispute: Dispute) -> str:
        """
        Build the prompt for dispute analysis.
        
        Args:
            dispute: The dispute to analyze
            
        Returns:
            Formatted prompt string
        """
        evidence_summary = ""
        if dispute.evidence_items:
            evidence_summary = "\n".join([
                f"- {item.get('type', 'Unknown')}: {json.dumps(item.get('data', {}), indent=2)} "
                f"(strength: {item.get('strength_score', 0):.2f})"
                for item in dispute.evidence_items
            ])
        else:
            evidence_summary = "No evidence uploaded yet."
        
        prompt = f"""You are an expert PayPal dispute analyst. Analyze this dispute and provide structured reasoning.

**Dispute Details:**
- ID: {dispute.paypal_dispute_id}
- Buyer: {dispute.buyer_name} ({dispute.buyer_email})
- Amount: ${dispute.amount} {dispute.currency}
- Reason: {dispute.reason.value}
- Status: {dispute.status.value}
- Transaction: {dispute.transaction_id}
- Order: {dispute.order_id}

**Evidence Available:**
{evidence_summary}

**Your Task:**
Analyze this dispute from the seller's perspective and provide:
1. Evidence that HELPS the seller (what they have going for them)
2. Evidence that HURTS the seller (gaps, buyer claims, weak points)
3. What additional evidence the seller should gather
4. Your estimated probability that the seller will WIN (0.0 to 1.0)
5. Your confidence in this analysis (low/medium/high)
6. A clear 2-3 sentence summary in plain English explaining why you think the seller will win or lose

Consider factors like:
- Tracking and delivery proof
- Item descriptions and buyer expectations
- Communication history
- Seller response time
- Type of dispute reason
- PayPal's typical ruling patterns for this dispute type
"""
        return prompt
    
    async def _call_gemini_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ) -> Optional[StructuredDisputeAnalysis]:
        """
        Call Gemini API with exponential backoff retry.
        
        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            
        Returns:
            Parsed StructuredDisputeAnalysis or None if all retries fail
        """
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Gemini API (attempt {attempt + 1}/{max_retries})...")
                
                # Generate content with JSON schema
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=StructuredDisputeAnalysis,
                        temperature=0.3,  # Lower temperature for more consistent structured output
                    )
                )
                
                # Parse the JSON response
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                analysis_dict = json.loads(response.text)
                analysis = StructuredDisputeAnalysis(**analysis_dict)
                
                logger.info(f"Successfully parsed Gemini response: {analysis.confidence} confidence")
                return analysis
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error("All retry attempts failed due to JSON parse errors")
                    return None
                    
            except ValidationError as e:
                logger.warning(f"Pydantic validation error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error("All retry attempts failed due to validation errors")
                    return None
                    
            except Exception as e:
                logger.warning(f"API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"All retry attempts failed: {e}")
                    return None
        
        return None
    
    def _calculate_heuristic_probability(self, dispute: Dispute) -> float:
        """
        Calculate a simple heuristic probability as fallback.
        
        Args:
            dispute: The dispute to analyze
            
        Returns:
            Win probability between 0.0 and 1.0
        """
        # Simple heuristic based on evidence strength
        if not dispute.evidence_items:
            return 0.3  # Low probability with no evidence
        
        avg_strength = sum(
            item.get("strength_score", 0.5) 
            for item in dispute.evidence_items
        ) / len(dispute.evidence_items)
        
        # Adjust by dispute reason
        reason_adjustments = {
            "UNAUTHORISED": -0.2,  # Hard to fight
            "MERCHANDISE_OR_SERVICE_NOT_RECEIVED": 0.0,  # Neutral
            "MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED": -0.1,  # Slightly harder
            "DUPLICATE_TRANSACTION": 0.1,  # Easier with proof
        }
        
        adjustment = reason_adjustments.get(dispute.reason.value, 0.0)
        probability = avg_strength + adjustment
        
        # Clamp to reasonable range
        return max(0.1, min(0.9, probability))
    
    def _create_fallback_analysis(self, dispute: Dispute) -> StructuredDisputeAnalysis:
        """
        Create a deterministic fallback analysis when Gemini fails.
        
        Args:
            dispute: The dispute to analyze
            
        Returns:
            Basic structured analysis based on heuristics
        """
        logger.warning("Using fallback heuristic analysis")
        
        heuristic_prob = self._calculate_heuristic_probability(dispute)
        
        # Generate basic evidence analysis
        evidence_for = []
        evidence_against = []
        missing_evidence = []
        
        if dispute.evidence_items:
            for item in dispute.evidence_items:
                ev_type = item.get("type", "Unknown")
                strength = item.get("strength_score", 0.5)
                
                if strength >= 0.7:
                    evidence_for.append({
                        "item": ev_type,
                        "why_it_helps": f"Strong {ev_type.lower()} evidence provided",
                        "weight": "strong" if strength >= 0.85 else "moderate"
                    })
                elif strength < 0.4:
                    evidence_against.append({
                        "item": ev_type,
                        "why_it_hurts": f"Weak {ev_type.lower()} evidence",
                        "weight": "moderate"
                    })
        
        if not any(item.get("type") == "TRACKING_INFO" for item in dispute.evidence_items):
            missing_evidence.append("Tracking information with delivery confirmation")
        
        if not any(item.get("type") == "PROOF_OF_DELIVERY" for item in dispute.evidence_items):
            missing_evidence.append("Proof of delivery with signature")
        
        if not any(item.get("type") == "BUYER_COMMUNICATION" for item in dispute.evidence_items):
            missing_evidence.append("Communication history with the buyer")
        
        # Determine confidence
        if dispute.evidence_items and len(dispute.evidence_items) >= 3:
            confidence = "medium"
        elif dispute.evidence_items and len(dispute.evidence_items) >= 1:
            confidence = "low"
        else:
            confidence = "low"
        
        # Generate reasoning
        if heuristic_prob >= 0.7:
            reasoning = f"Based on the available evidence, you have a strong case with approximately {heuristic_prob:.0%} estimated win probability. The evidence provided supports your position. However, consider gathering additional documentation to strengthen your case further."
        elif heuristic_prob >= 0.4:
            reasoning = f"This dispute presents a mixed case with approximately {heuristic_prob:.0%} estimated win probability. While you have some supporting evidence, there are gaps that could weaken your position. Gathering the missing evidence could improve your chances significantly."
        else:
            reasoning = f"This appears to be a challenging case with approximately {heuristic_prob:.0%} estimated win probability. The available evidence may not be sufficient to win. Consider whether the cost of fighting is justified or if a refund would be more practical."
        
        return StructuredDisputeAnalysis(
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            missing_evidence=missing_evidence,
            llm_win_probability=heuristic_prob,
            confidence=confidence,
            reasoning_summary=reasoning
        )
    
    async def analyze_dispute(
        self,
        dispute: Dispute,
        persist: bool = True,
        heuristic_weight: float = 0.6,
        llm_weight: float = 0.4
    ) -> AgentAnalysis:
        """
        Analyze a dispute and return structured analysis.
        
        Args:
            dispute: The dispute to analyze
            persist: Whether to persist the analysis to the database
            heuristic_weight: Weight for heuristic probability (default 0.6)
            llm_weight: Weight for LLM probability (default 0.4)
            
        Returns:
            AgentAnalysis document with the structured reasoning
        """
        logger.info(f"Analyzing dispute {dispute.paypal_dispute_id}...")
        
        # Calculate heuristic probability first (always available as fallback)
        heuristic_prob = calculate_heuristic_probability(dispute)
        logger.info(f"Heuristic probability: {heuristic_prob:.2%}")
        
        # Build prompt
        prompt = self._build_analysis_prompt(dispute)
        
        # Try to get structured analysis from Gemini
        structured = await self._call_gemini_with_retry(prompt)
        
        # Determine LLM probability and blended result
        if structured is None:
            # Fall back to heuristic if Gemini fails
            logger.warning("Gemini failed, using heuristic-only probability")
            structured = self._create_fallback_analysis(dispute)
            llm_prob = None
            blended_prob = heuristic_prob  # Use heuristic only
        else:
            # Blend heuristic with LLM
            llm_prob = structured.llm_win_probability
            blended_prob = blend_probabilities(
                heuristic_prob, 
                llm_prob,
                heuristic_weight=heuristic_weight,
                llm_weight=llm_weight
            )
            logger.info(f"LLM probability: {llm_prob:.2%}, Blended: {blended_prob:.2%}")
        
        # Calculate expected values using the blended business rule
        fighting_cost = settings.fighting_cost
        risk_buffer = settings.risk_buffer
        
        refund_loss = dispute.amount
        fight_expected_loss = (
            Decimal(str(1 - blended_prob)) * dispute.amount + fighting_cost
        )
        
        # Make decision: FIGHT if win_prob * amount > fighting_cost + risk_buffer
        should_fight = (
            blended_prob * float(dispute.amount) 
            > float(fighting_cost + risk_buffer)
        )
        
        decision = AgentDecision.FIGHT if should_fight else AgentDecision.REFUND
        
        # Convert confidence to numeric for storage
        confidence_map = {
            ConfidenceLevel.LOW: 0.5,
            ConfidenceLevel.MEDIUM: 0.75,
            ConfidenceLevel.HIGH: 0.9
        }
        numeric_confidence = confidence_map.get(structured.confidence, 0.75)
        
        # Build reasoning steps
        reasoning_steps = [
            f"Heuristic scorer: {heuristic_prob:.0%} win probability",
        ]
        
        if llm_prob is not None:
            reasoning_steps.append(f"LLM analysis: {llm_prob:.0%} win probability ({structured.confidence.value} confidence)")
            reasoning_steps.append(f"Blended probability (60% heuristic, 40% LLM): {blended_prob:.0%}")
        else:
            reasoning_steps.append("LLM analysis unavailable, using heuristic only")
        
        reasoning_steps.extend([
            f"LLM analyzed {len(dispute.evidence_items)} evidence items",
            f"Found {len(structured.evidence_for)} supporting factors",
            f"Identified {len(structured.evidence_against)} concerning factors",
            f"Recommended gathering {len(structured.missing_evidence)} additional pieces of evidence",
            f"Expected loss if we fight: ${fight_expected_loss:.2f}",
            f"Expected loss if we refund: ${refund_loss:.2f}",
            structured.reasoning_summary
        ])
        
        # Generate drafted response
        if decision == AgentDecision.FIGHT:
            drafted_response = f"We respectfully dispute this claim. {structured.reasoning_summary} We have provided supporting evidence and are prepared to demonstrate that we fulfilled our obligations as a seller."
        else:
            drafted_response = f"We want to resolve this matter fairly. {structured.reasoning_summary} We are willing to work with the buyer to find an amicable solution."
        
        # Create AgentAnalysis document
        analysis = AgentAnalysis(
            dispute_id=str(dispute.id),
            decision=decision,
            confidence=numeric_confidence,
            win_probability=blended_prob,
            heuristic_probability=heuristic_prob,
            llm_probability=llm_prob,
            refund_loss=refund_loss,
            fight_expected_loss=fight_expected_loss,
            fighting_cost=fighting_cost,
            evidence_items=dispute.evidence_items,
            drafted_response=drafted_response,
            reasoning_steps=reasoning_steps,
            risks=[item.why_it_hurts for item in structured.evidence_against] if structured.evidence_against else []
        )
        
        if persist:
            # Save analysis
            await analysis.insert()
            logger.info(f"Saved analysis {analysis.id} for dispute {dispute.paypal_dispute_id}")
            
            # Update dispute with analysis reference
            dispute.latest_analysis_id = str(analysis.id)
            await dispute.save()
            
            # Create audit log
            audit = AuditLog(
                action="agent_analysis_completed",
                dispute_id=str(dispute.id),
                actor="gemini_agent",
                reasoning=structured.reasoning_summary,
                metadata={
                    "decision": decision.value,
                    "confidence": structured.confidence.value,
                    "heuristic_probability": heuristic_prob,
                    "llm_probability": llm_prob,
                    "blended_probability": blended_prob,
                    "evidence_for_count": len(structured.evidence_for),
                    "evidence_against_count": len(structured.evidence_against),
                    "missing_evidence_count": len(structured.missing_evidence)
                }
            )
            await audit.insert()
            logger.info(f"Created audit log for analysis")
        
        return analysis


# Convenience function for easy imports
async def analyze_dispute(dispute: Dispute, persist: bool = True) -> AgentAnalysis:
    """
    Analyze a dispute using the Gemini analyzer.
    
    Args:
        dispute: The dispute to analyze
        persist: Whether to persist to database
        
    Returns:
        AgentAnalysis document
    """
    analyzer = GeminiAnalyzer()
    return await analyzer.analyze_dispute(dispute, persist=persist)
