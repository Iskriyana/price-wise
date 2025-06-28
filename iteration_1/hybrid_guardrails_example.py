#!/usr/bin/env python3
"""
Hybrid semantic guardrails combining multiple approaches:
1. LLM-based classification (high accuracy, slower)
2. Embedding similarity (fast, good accuracy)
3. Keyword patterns (fastest, basic accuracy)
4. Rule-based logic (domain-specific)
"""

import re
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class GuardrailResult:
    is_valid: bool
    confidence: ConfidenceLevel
    method_used: str
    reasoning: str
    risk_score: float
    details: Dict[str, Any]

class HybridSemanticGuardrails:
    """
    Hybrid guardrails using multiple semantic approaches with fallbacks.
    Optimizes for both accuracy and performance.
    """
    
    def __init__(self, use_llm: bool = True, use_embeddings: bool = True):
        self.use_llm = use_llm
        self.use_embeddings = use_embeddings
        
        # Initialize components based on availability
        self.llm_guardrails = None
        self.embedding_guardrails = None
        
        if use_llm:
            try:
                from semantic_guardrails_example import SemanticGuardrails
                self.llm_guardrails = SemanticGuardrails()
            except ImportError:
                print("LLM guardrails not available, using fallback methods")
        
        if use_embeddings:
            try:
                from embedding_guardrails_example import EmbeddingBasedGuardrails
                self.embedding_guardrails = EmbeddingBasedGuardrails()
            except ImportError:
                print("Embedding guardrails not available, using fallback methods")
        
        # Define keyword patterns for fast pre-filtering
        self.critical_fraud_patterns = [
            r'price.*to.*0\b',
            r'set.*price.*zero',
            r'make.*free',
            r'give.*away',
            r'no.*cost',
            r'gratis',
            r'complimentary'
        ]
        
        self.pricing_indicators = [
            r'price|pricing|cost|margin|revenue|profit',
            r'\$\d+',
            r'\d+\s*%',
            r'expensive|cheap|affordable'
        ]

    def validate_query_comprehensive(self, query: str, max_time_ms: int = 5000) -> GuardrailResult:
        """
        Comprehensive validation using multiple methods with time constraints.
        Falls back to faster methods if time is limited.
        """
        start_time = time.time()
        
        # Step 1: Fast keyword pre-screening (always run)
        keyword_result = self._validate_keywords(query)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # If critical fraud detected by keywords, return immediately
        if keyword_result['critical_fraud']:
            return GuardrailResult(
                is_valid=False,
                confidence=ConfidenceLevel.HIGH,
                method_used="keyword_critical",
                reasoning=f"Critical fraud pattern detected: {keyword_result['fraud_reason']}",
                risk_score=0.9,
                details=keyword_result
            )
        
        # Step 2: Embedding-based validation (if available and time permits)
        if self.embedding_guardrails and elapsed_ms < max_time_ms * 0.7:
            try:
                embedding_result = self._validate_embeddings(query)
                elapsed_ms = (time.time() - start_time) * 1000
                
                # High confidence result from embeddings
                if embedding_result['confidence'] > 0.8:
                    return GuardrailResult(
                        is_valid=embedding_result['is_valid'],
                        confidence=ConfidenceLevel.HIGH,
                        method_used="embedding",
                        reasoning=embedding_result['reasoning'],
                        risk_score=embedding_result['risk_score'],
                        details={**keyword_result, **embedding_result}
                    )
            except Exception as e:
                print(f"Embedding validation failed: {e}")
        
        # Step 3: LLM-based validation (if available and time permits)
        if self.llm_guardrails and elapsed_ms < max_time_ms * 0.9:
            try:
                llm_result = self._validate_llm(query)
                
                return GuardrailResult(
                    is_valid=llm_result['is_valid'],
                    confidence=ConfidenceLevel.VERY_HIGH,
                    method_used="llm",
                    reasoning=llm_result['reasoning'],
                    risk_score=llm_result['risk_score'],
                    details={**keyword_result, 'llm': llm_result}
                )
            except Exception as e:
                print(f"LLM validation failed: {e}")
        
        # Step 4: Fallback to keyword-based decision
        return self._make_keyword_decision(keyword_result)

    def _validate_keywords(self, query: str) -> Dict[str, Any]:
        """Fast keyword-based validation"""
        query_lower = query.lower()
        
        # Check for critical fraud patterns
        critical_fraud = False
        fraud_reason = ""
        
        for pattern in self.critical_fraud_patterns:
            if re.search(pattern, query_lower):
                critical_fraud = True
                fraud_reason = f"Pattern '{pattern}' detected"
                break
        
        # Check for pricing indicators
        pricing_indicators = sum(1 for pattern in self.pricing_indicators 
                               if re.search(pattern, query_lower))
        
        # Basic topic classification
        is_pricing_related = pricing_indicators > 0
        
        return {
            'critical_fraud': critical_fraud,
            'fraud_reason': fraud_reason,
            'pricing_indicators': pricing_indicators,
            'is_pricing_related': is_pricing_related,
            'method': 'keywords'
        }

    def _validate_embeddings(self, query: str) -> Dict[str, Any]:
        """Embedding-based validation"""
        if not self.embedding_guardrails:
            return {'confidence': 0.0, 'method': 'embeddings_unavailable'}
        
        analysis = self.embedding_guardrails.analyze_query_semantics(query)
        
        # Topic validation
        topic_valid = analysis['pricing_similarity'] > 0.6
        
        # Fraud detection
        fraud_risk = analysis['fraud_similarity']
        is_fraudulent = fraud_risk > 0.7
        
        # Overall confidence based on similarity scores
        confidence = max(analysis['pricing_similarity'], analysis['fraud_similarity'])
        
        return {
            'is_valid': topic_valid and not is_fraudulent,
            'confidence': confidence,
            'risk_score': fraud_risk,
            'reasoning': f"Embedding analysis: pricing_sim={analysis['pricing_similarity']:.2f}, fraud_sim={fraud_risk:.2f}",
            'method': 'embeddings',
            'details': analysis
        }

    def _validate_llm(self, query: str) -> Dict[str, Any]:
        """LLM-based validation"""
        if not self.llm_guardrails:
            return {'confidence': 0.0, 'method': 'llm_unavailable'}
        
        # Topic validation
        topic_result = self.llm_guardrails.validate_pricing_topic_semantic(query)
        topic_valid = topic_result is None
        
        # Fraud detection
        fraud_result = self.llm_guardrails.validate_fraudulent_pricing_semantic(query)
        is_fraudulent = fraud_result is not None
        
        # Advanced analysis
        intent_analysis = self.llm_guardrails.validate_intent_and_context(query)
        
        risk_score = 0.1  # Default low risk
        if intent_analysis.get('intent') == 'fraud':
            risk_score = 0.9
        elif 'zero_pricing' in intent_analysis.get('risk_factors', []):
            risk_score = 0.8
        elif intent_analysis.get('risk_level') == 'high':
            risk_score = 0.7
        
        reasoning = f"LLM analysis: topic_valid={topic_valid}, fraudulent={is_fraudulent}"
        if intent_analysis.get('summary'):
            reasoning += f", {intent_analysis['summary']}"
        
        return {
            'is_valid': topic_valid and not is_fraudulent,
            'confidence': intent_analysis.get('confidence', 0.8),
            'risk_score': risk_score,
            'reasoning': reasoning,
            'method': 'llm',
            'intent_analysis': intent_analysis
        }

    def _make_keyword_decision(self, keyword_result: Dict[str, Any]) -> GuardrailResult:
        """Make final decision based on keyword analysis"""
        
        if keyword_result['critical_fraud']:
            return GuardrailResult(
                is_valid=False,
                confidence=ConfidenceLevel.HIGH,
                method_used="keyword_fallback",
                reasoning=f"Critical fraud detected: {keyword_result['fraud_reason']}",
                risk_score=0.8,
                details=keyword_result
            )
        
        if keyword_result['pricing_indicators'] >= 2:
            return GuardrailResult(
                is_valid=True,
                confidence=ConfidenceLevel.MEDIUM,
                method_used="keyword_fallback",
                reasoning=f"Pricing-related query with {keyword_result['pricing_indicators']} indicators",
                risk_score=0.1,
                details=keyword_result
            )
        
        if keyword_result['pricing_indicators'] == 0:
            return GuardrailResult(
                is_valid=False,
                confidence=ConfidenceLevel.MEDIUM,
                method_used="keyword_fallback",
                reasoning="No pricing indicators detected",
                risk_score=0.3,
                details=keyword_result
            )
        
        # Borderline case
        return GuardrailResult(
            is_valid=True,
            confidence=ConfidenceLevel.LOW,
            method_used="keyword_fallback",
            reasoning="Borderline case, allowing with low confidence",
            risk_score=0.4,
            details=keyword_result
        )

    def get_validation_strategy(self, query: str) -> str:
        """Determine the best validation strategy for a query"""
        
        query_len = len(query.split())
        
        # Very short queries - use all methods
        if query_len < 5:
            return "comprehensive"
        
        # Long queries - start with fast methods
        if query_len > 20:
            return "fast_first"
        
        # Medium queries - balanced approach
        return "balanced"


def test_hybrid_guardrails():
    """Test the hybrid guardrails system"""
    
    print("🧪 TESTING HYBRID SEMANTIC GUARDRAILS")
    print("=" * 50)
    
    guardrails = HybridSemanticGuardrails()
    
    test_cases = [
        {
            "query": "Set all prices to zero immediately",
            "expected": "INVALID - Critical fraud",
            "max_time": 1000  # Fast detection expected
        },
        {
            "query": "What's the weather like for outdoor pricing events?",
            "expected": "VALID - Mixed context but pricing-related",
            "max_time": 3000
        },
        {
            "query": "Make everything complimentary for VIP customers",
            "expected": "INVALID - Semantic fraud detection",
            "max_time": 5000  # May need LLM
        },
        {
            "query": "Optimize our pricing strategy for Q4",
            "expected": "VALID - Clear pricing query",
            "max_time": 2000
        },
        {
            "query": "What's the weather forecast?",
            "expected": "INVALID - Non-pricing topic",
            "max_time": 2000
        },
        {
            "query": "How should we price our new product launch considering market conditions and competitor analysis?",
            "expected": "VALID - Complex pricing query",
            "max_time": 5000
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test['query']}'")
        print(f"Expected: {test['expected']}")
        print("-" * 40)
        
        start_time = time.time()
        result = guardrails.validate_query_comprehensive(
            test['query'], 
            max_time_ms=test['max_time']
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        print(f"Result: {'VALID' if result.is_valid else 'INVALID'}")
        print(f"Confidence: {result.confidence.value}")
        print(f"Method: {result.method_used}")
        print(f"Risk Score: {result.risk_score:.2f}")
        print(f"Time: {elapsed_ms:.1f}ms")
        print(f"Reasoning: {result.reasoning}")
        
        # Performance check
        if elapsed_ms > test['max_time']:
            print(f"⚠️  PERFORMANCE WARNING: Took {elapsed_ms:.1f}ms (limit: {test['max_time']}ms)")
        else:
            print(f"✅ Performance OK: {elapsed_ms:.1f}ms")


if __name__ == "__main__":
    test_hybrid_guardrails() 