#!/usr/bin/env python3
"""
Semantic guardrails for the pricing agent.
Provides LLM-based validation as a fallback to keyword-based checks.
"""

import os
import re
import logging
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

# Configure logging
logger = logging.getLogger(__name__)

class SemanticGuardrails:
    """
    Semantic validation using LLM-based classification.
    Designed to work alongside existing keyword-based guardrails.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.llm = None
        
        # Initialize LLM if API key is available
        if self.openai_api_key:
            try:
                self.llm = ChatOpenAI(
                    model="gpt-4o",         # High-quality model for better semantic understanding
                    temperature=0.0,        # Deterministic for guardrails
                    api_key=self.openai_api_key,
                    timeout=10.0            # Slightly longer timeout for GPT-4o
                )
            except Exception as e:
                logger.warning(f"Could not initialize LLM for semantic guardrails: {e}")
        
        # Fast keyword patterns for pre-filtering
        self.critical_fraud_keywords = [
            'price to 0', 'price to zero', 'set price to 0', 'set price to zero',
            'make free', 'make it free', 'price at 0', 'price at zero',
            'give away', 'no cost', 'zero cost', 'free of charge'
        ]

    def validate_pricing_topic_semantic(self, query: str) -> Optional[str]:
        """
        Semantic topic validation using LLM.
        Returns None if valid, error message if invalid.
        """
        if not self.llm:
            return None  # Fall back to keyword validation
        
        system_prompt = """You are a pricing topic classifier. Determine if a user query is related to pricing, costs, or business financial decisions.

PRICING-RELATED topics include:
- Product pricing strategies and recommendations
- Cost analysis, margins, and profitability
- Competitive pricing and market positioning
- Revenue optimization and financial impact
- Price adjustments and promotional pricing
- Questions about pricing scenarios or strategies

NON-PRICING topics include:
- Weather, sports, entertainment, news
- Technical support or software tutorials  
- Medical advice or health information
- Travel planning or logistics
- General product information without pricing context
- Customer service issues unrelated to pricing

Be generous with pricing-related queries. If there's ANY reasonable pricing context, classify as VALID.

Respond with ONLY:
- "VALID" if the query is pricing-related
- "INVALID: [brief reason]" if the query is not pricing-related"""

        user_prompt = f"Classify this query: '{query}'"
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            result = response.content.strip()
            
            if result.startswith("INVALID"):
                reason = result.replace("INVALID:", "").strip()
                return f"I specialize in pricing analysis and recommendations. Your query appears to be about {reason.lower()}, which is outside my expertise. Please ask questions related to product pricing, cost optimization, or pricing strategies."
            
            return None  # Valid pricing query
            
        except Exception as e:
            logger.error(f"LLM topic validation failed: {e}")
            return None  # Fall back to keyword validation

    def validate_fraudulent_pricing_semantic(self, query: str) -> Optional[str]:
        """
        Semantic fraud detection using LLM.
        Returns None if safe, error message if potentially fraudulent.
        """
        # Fast keyword pre-check for obvious fraud
        query_lower = query.lower()
        for keyword in self.critical_fraud_keywords:
            if keyword in query_lower:
                return "I cannot process requests for zero or extremely low pricing as this may indicate an error or unauthorized activity. Such pricing decisions require special authorization and manual review."
        
        if not self.llm:
            return None  # Fall back to keyword validation
        
        system_prompt = """You are a fraud detection system for pricing requests. Identify potentially dangerous or unauthorized pricing requests.

FRAUDULENT/DANGEROUS patterns include:
- Requests to set prices to zero or near-zero ($0, "free", "gratis", "complimentary", "no charge")
- Attempts to manipulate pricing for personal gain or system gaming
- Requests that would clearly damage business revenue without justification
- Language suggesting deception, unauthorized activity, or circumventing controls
- Bulk pricing manipulation that seems suspicious

LEGITIMATE pricing requests include:
- Normal business pricing adjustments with rationale
- Competitive pricing analysis and benchmarking
- Margin optimization and revenue strategies
- Promotional pricing with clear business justification
- Market positioning and value-based pricing
- Analytical questions about pricing scenarios (not actual requests to implement)
- Academic or strategic pricing discussions

Key distinction: Questions ABOUT pricing scenarios are legitimate, but requests TO IMPLEMENT dangerous pricing are not.

Respond with ONLY:
- "SAFE" if the query is a legitimate pricing request
- "DANGEROUS: [brief reason]" if the query appears fraudulent or dangerous"""

        user_prompt = f"Analyze this pricing request: '{query}'"
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            result = response.content.strip()
            
            if result.startswith("DANGEROUS"):
                reason = result.replace("DANGEROUS:", "").strip()
                return f"I cannot process this request as it appears to involve {reason.lower()}. Such pricing decisions require special authorization and manual review. Please contact your supervisor or the pricing committee for guidance on exceptional pricing scenarios."
            
            return None  # Safe pricing request
            
        except Exception as e:
            logger.error(f"LLM fraud detection failed: {e}")
            return None  # Fall back to keyword validation

    def is_available(self) -> bool:
        """Check if semantic validation is available"""
        return self.llm is not None

    def get_status(self) -> Dict[str, Any]:
        """Get status of semantic guardrails"""
        return {
            "llm_available": self.llm is not None,
            "model": "gpt-4o" if self.llm else None,
            "api_key_configured": bool(self.openai_api_key)
        } 