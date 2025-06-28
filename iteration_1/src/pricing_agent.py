"""
RAG-powered Pricing Agent for Iteration 1 with Enhanced Guardrails and Approval Workflows

This module implements a workflow-based agent that uses Retrieval-Augmented Generation
to answer pricing questions by retrieving relevant product data and generating 
informed recommendations with comprehensive guardrails and approval workflows.
"""
import os
import logging
import uuid
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from src.models import (
    PricingQuery, PricingRecommendation, ProductInfo, ApprovalLevel, 
    ApprovalStatus, RiskLevel, GuardrailViolation, ApprovalRequest, SystemStatus
)
from src.data_loader import PricingDataLoader
from src.vector_store import PricingVectorStore
from src.simple_retriever import SimplePricingRetriever
from src.prompts import (
    PRICING_SYSTEM_PROMPT, create_user_prompt, create_full_context,
    create_fallback_reasoning, FALLBACK_RECOMMENDATIONS
)

logger = logging.getLogger(__name__)


class EnhancedPricingRAGAgent:
    """Enhanced RAG-powered agent for pricing questions with guardrails and approval workflows"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = None
        self.data_loader = PricingDataLoader()
        self.vector_store = PricingVectorStore()
        self.simple_retriever = SimplePricingRetriever()
        self.use_vector_store = True
        self.initialized = False
        
        # In-memory storage for recommendations and approvals (in production, use database)
        self.active_recommendations: Dict[str, PricingRecommendation] = {}
        self.approval_history: List[ApprovalRequest] = []
        
        # Guardrail configuration
        self.guardrail_config = {
            "max_price_change_percent": 50.0,
            "min_margin_percent": 10.0,
            "max_margin_percent": 80.0,
            "price_below_cost_multiplier": 1.05,  # 5% minimum markup
            "high_risk_price_change": 25.0,
            "critical_risk_price_change": 40.0,
            "low_confidence_threshold": 0.6,
            "medium_confidence_threshold": 0.8,
            
            # New guardrails for fraud and high-value items
            "min_absolute_price": 0.50,  # Minimum price of $0.50
            "high_value_item_threshold": 500.0,  # Items over $500 are high-value
            "max_absolute_price_change": 100.0  # Absolute price changes over $100 are high-risk
        }
        
    def initialize(self) -> None:
        """Initialize the agent with data loading and vector store setup"""
        try:
            # Initialize LLM
            if self.openai_api_key:
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.1,
                    openai_api_key=self.openai_api_key
                )
                logger.info("Initialized OpenAI LLM")
            else:
                logger.warning("No OpenAI API key provided - will use fallback mode")
                
            # Load pricing data
            products = self.data_loader.load_data()
            logger.info(f"Loaded {len(products)} products")
            
            # Try to initialize vector store
            try:
                self.vector_store.initialize(self.openai_api_key)
                collection_info = self.vector_store.get_collection_info()
                if collection_info.get("count", 0) == 0:
                    logger.info("Vector store is empty, adding products...")
                    self.vector_store.add_products(products)
                else:
                    logger.info(f"Vector store already contains {collection_info['count']} products")
                
                self.use_vector_store = True
                logger.info("Vector store initialized successfully")
                
            except Exception as e:
                logger.warning(f"Vector store failed to initialize: {e}")
                logger.info("Falling back to simple text-based retrieval")
                self.use_vector_store = False
                
            # Initialize simple retriever as fallback
            self.simple_retriever.initialize(products)
                
            self.initialized = True
            logger.info("Enhanced pricing agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize pricing agent: {e}")
            raise
    
    def _validate_pricing_topic(self, query: PricingQuery) -> Optional[str]:
        """
        Validate that the query is about pricing and not other topics.
        Returns None if valid, error message if invalid.
        """
        query_text = query.query.lower()
        
        # Define pricing-related keywords
        pricing_keywords = [
            'price', 'pricing', 'cost', 'margin', 'discount', 'markup', 'revenue',
            'profit', 'expensive', 'cheap', 'affordable', 'competitive', 'sale',
            'promotion', 'offer', 'value', 'rate', 'fee', 'charge', 'bill',
            'quote', 'estimate', 'budget', 'financial', 'money', 'dollar',
            'cents', 'currency', 'payment', 'recommendation', 'suggest',
            'optimize', 'adjust', 'increase', 'decrease', 'reduce', 'raise'
        ]
        
        # Define non-pricing topics that should be rejected
        # NOTE: Be very careful here - only reject topics that are clearly NOT about pricing
        non_pricing_keywords = [
            'weather forecast', 'temperature today', 'will it rain', 'snow tomorrow', 
            'sunny weather', 'cloudy skies',  # More specific weather terms
            'store hours', 'contact information', 'phone number', 'email address',
            'recipe for', 'cooking instructions', 'restaurant menu',
            'flight booking', 'hotel reservation', 'vacation planning',
            'medical advice', 'health symptoms', 'doctor appointment',
            'movie times', 'concert tickets', 'entertainment schedule',
            'programming tutorial', 'software installation', 'computer repair'
        ]
        
        # Check for explicit non-pricing topics
        for keyword in non_pricing_keywords:
            if keyword in query_text:
                return f"I apologize, but I can only assist with pricing-related inquiries. Your question appears to be about '{keyword}', which is outside my scope of expertise. Please ask questions related to product pricing, cost analysis, or pricing recommendations."
        
        # Check if query contains pricing-related content
        has_pricing_content = any(keyword in query_text for keyword in pricing_keywords)
        
        # Additional check for common pricing patterns
        pricing_patterns = [
            r'\$\d+',  # Dollar amounts like $50
            r'\d+\s*cents?',  # Cent amounts
            r'\d+\s*%',  # Percentages
            r'how much',  # Common pricing question
            r'what.*cost',  # Cost questions
            r'should.*price',  # Price recommendation questions
        ]
        
        has_pricing_pattern = any(re.search(pattern, query_text) for pattern in pricing_patterns)
        
        if not (has_pricing_content or has_pricing_pattern):
            return "I specialize in pricing analysis and recommendations. Please ask questions related to product pricing, cost optimization, margin analysis, or pricing strategies. For other inquiries, please consult the appropriate specialist."
        
        return None  # Valid pricing query
    
    def _validate_fraudulent_pricing(self, query: PricingQuery) -> Optional[str]:
        """
        Detect potentially fraudulent pricing requests.
        Returns None if valid, error message if potentially fraudulent.
        """
        query_text = query.query.lower()
        
        # Extract potential price values from the query
        price_patterns = [
            # Zero pricing patterns (CRITICAL)
            r'price.*to.*0\b',  # "price to 0", "set price to 0"
            r'price.*at.*0\b',  # "price at 0", "price it at 0"
            r'reduce.*price.*to.*0\b',  # "reduce price to 0"
            r'make.*price.*0\b',  # "make price 0"
            r'set.*price.*0\b',  # "set price 0"
            r'\$0\b',  # "$0" (standalone)
            r'\bzero\s*dollars?\b',  # "zero dollars"
            r'price.*zero\b',  # "price zero", "price to zero"
            r'cost.*zero\b',  # "cost zero"
            
            # Very low pricing patterns
            r'\$0\.0[1-9]',  # $0.01 to $0.09
            r'\$0\.1[0-9]',  # $0.10 to $0.19
            r'\$0\.[2-4][0-9]',  # $0.20 to $0.49
            r'0\.0[1-9]\s*dollars?',  # 0.01 to 0.09 dollars
            r'0\.[1-4][0-9]\s*dollars?',  # 0.10 to 0.49 dollars
            r'[1-4]?[0-9]\s*cents?',  # 1 to 49 cents
            r'one\s*cent',  # "one cent"
            r'penny',  # "penny"
            r'almost\s*free',  # "almost free"
            r'nearly\s*zero',  # "nearly zero"
            r'minimal\s*price',  # "minimal price"
        ]
        
        # Check for suspicious pricing patterns
        for pattern in price_patterns:
            if re.search(pattern, query_text):
                return "I cannot process requests for extremely low pricing (under $0.50) as this may indicate an error or unauthorized activity. Such pricing decisions require special authorization and manual review. Please contact your supervisor or the pricing committee for assistance with exceptional pricing scenarios."
        
        # Check for explicit requests to set very low prices
        suspicious_phrases = [
            # Zero price phrases (CRITICAL)
            'price to 0',
            'price at 0', 
            'price to zero',
            'price at zero',
            'reduce price to 0',
            'reduce price to zero',
            'set price to 0',
            'set price to zero',
            'make price 0',
            'make price zero',
            'price all items to 0',
            'price everything to 0',
            
            # Very low price phrases
            'set price to 1 cent',
            'make it 1 cent',
            'price it at 1 cent',
            'sell for 1 cent',
            'charge 1 cent',
            'cost 1 cent',
            'practically free',
            'give away',
            'free of charge'
        ]
        
        for phrase in suspicious_phrases:
            if phrase in query_text:
                return "I cannot assist with pricing requests that appear to be non-commercial or potentially unauthorized. Pricing decisions must align with business objectives and regulatory requirements. Please consult with management for guidance on exceptional pricing scenarios."
        
        return None  # No fraudulent patterns detected

    def _validate_revenue_maximization(self, query: PricingQuery, recommendation: PricingRecommendation) -> Optional[str]:
        """
        Validate that the recommendation will result in positive revenue impact.
        Uses price elasticity to calculate realistic demand changes.
        Returns None if valid, error message if revenue impact is negative.
        """
        if not recommendation.product_info or not recommendation.recommended_price:
            return None  # Cannot validate without product info
        
        product = recommendation.product_info[0]
        current_price = product.current_price
        recommended_price = recommendation.recommended_price
        
        if current_price <= 0:
            return None  # Cannot calculate with invalid current price
        
        # Calculate price change percentage
        price_change_pct = ((recommended_price - current_price) / current_price) * 100
        
        # Calculate demand change using price elasticity
        # Formula: % change in demand = price_elasticity × % change in price
        demand_change_pct = product.price_elasticity * price_change_pct
        
        # Calculate new demand multiplier
        new_demand_multiplier = 1 + (demand_change_pct / 100)
        
        # Ensure demand doesn't go negative (minimum 5% of original demand)
        new_demand_multiplier = max(new_demand_multiplier, 0.05)
        
        # Calculate current and projected revenue
        recent_sales = sum(product.hourly_sales) if product.hourly_sales else 0
        daily_sales_estimate = recent_sales * 4  # Extrapolate 6h to 24h
        
        current_daily_revenue = current_price * daily_sales_estimate
        projected_daily_sales = daily_sales_estimate * new_demand_multiplier
        projected_daily_revenue = recommended_price * projected_daily_sales
        
        # Calculate monthly revenue impact
        daily_revenue_impact = projected_daily_revenue - current_daily_revenue
        monthly_revenue_impact = daily_revenue_impact * 30
        
        # Update the recommendation's financial impact with correct calculation
        recommendation.financial_impact = {
            "price_change_percent": price_change_pct,  # Keep signed value
            "price_change_amount": recommended_price - current_price,
            "estimated_monthly_revenue_impact": monthly_revenue_impact,
            "estimated_daily_sales": projected_daily_sales,
            "demand_change_percent": demand_change_pct,
            "current_daily_revenue": current_daily_revenue,
            "projected_daily_revenue": projected_daily_revenue
        }
        
        # Check if revenue impact is negative (allow zero impact for maintaining current price)
        if monthly_revenue_impact < -100:  # Allow small negative impacts due to rounding, but block significant losses
            return f"This recommendation would result in a negative monthly revenue impact of ${monthly_revenue_impact:,.2f}. Revenue maximization requires all price changes to generate positive revenue. Please consider alternative pricing strategies that account for demand elasticity (current elasticity: {product.price_elasticity})."
        
        # Update the recommendation's reasoning to include correct financial calculations
        financial_summary = f"""

FINANCIAL IMPACT ANALYSIS (Elasticity-Based):
• Price Change: ${current_price:.2f} → ${recommended_price:.2f} ({price_change_pct:+.1f}%)
• Demand Change: {demand_change_pct:+.1f}% (elasticity: {product.price_elasticity})
• Current Daily Sales: {daily_sales_estimate:.0f} units
• Projected Daily Sales: {projected_daily_sales:.0f} units
• Current Daily Revenue: ${current_daily_revenue:,.2f}
• Projected Daily Revenue: ${projected_daily_revenue:,.2f}
• Monthly Revenue Impact: ${monthly_revenue_impact:+,.2f}"""
        
        recommendation.reasoning += financial_summary
        
        return None  # Valid recommendation

    def process_query(self, query: PricingQuery) -> PricingRecommendation:
        """Process a pricing query using enhanced RAG workflow with guardrails"""
        if not self.initialized:
            raise ValueError("Agent not initialized. Call initialize() first.")
            
        try:
            # Input Validation Guardrails - Check these FIRST before any processing
            
            # Guardrail: Validate topic is pricing-related
            topic_validation_error = self._validate_pricing_topic(query)
            if topic_validation_error:
                return self._create_rejection_recommendation(
                    query, 
                    "TOPIC_VALIDATION_FAILED", 
                    topic_validation_error
                )
            
            # Guardrail: Check for potentially fraudulent pricing requests
            fraud_validation_error = self._validate_fraudulent_pricing(query)
            if fraud_validation_error:
                return self._create_rejection_recommendation(
                    query, 
                    "FRAUDULENT_PRICING_DETECTED", 
                    fraud_validation_error
                )
            
            # Generate unique recommendation ID
            recommendation_id = str(uuid.uuid4())
            
            # Step 1: Retrieve relevant context
            retrieval_context = self._retrieve_context(query)
            
            # Step 2: Apply mathematical validation/threshold checks
            validated_products = self._apply_business_rules(retrieval_context.relevant_products)
            
            # Step 3: Generate recommendation using LLM
            recommendation = self._generate_recommendation(query, retrieval_context, validated_products)
            
            # Step 3.5: Validate revenue maximization constraint
            revenue_validation_error = self._validate_revenue_maximization(query, recommendation)
            if revenue_validation_error:
                return self._create_rejection_recommendation(
                    query, 
                    "NEGATIVE_REVENUE_IMPACT", 
                    revenue_validation_error
                )
            
            # Step 4: Apply comprehensive guardrails and validation
            final_recommendation = self._apply_enhanced_guardrails(recommendation)
            
            # Step 5: Assess risk and determine approval requirements
            risk_assessed_recommendation = self._assess_risk_and_approval(final_recommendation)
            
            # Step 6: Set tracking information
            risk_assessed_recommendation.recommendation_id = recommendation_id
            risk_assessed_recommendation.created_by = query.requester_id
            
            # Store for approval workflow
            self.active_recommendations[recommendation_id] = risk_assessed_recommendation
            
            logger.info(f"Generated recommendation {recommendation_id} with risk level {risk_assessed_recommendation.risk_level}")
            
            return risk_assessed_recommendation
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise
    
    def _create_rejection_recommendation(self, query: PricingQuery, rejection_type: str, message: str) -> PricingRecommendation:
        """Create a recommendation object for rejected queries"""
        return PricingRecommendation(
            query=query.query,
            recommended_price=None,
            reasoning=message,
            confidence_score=0.0,
            product_info=[],
            market_context="Request rejected due to policy violation.",
            recommendation="Request cannot be processed due to policy violation.",
            guardrail_violations=[
                GuardrailViolation(
                    rule_name=rejection_type.lower(),
                    violation_type="policy_violation",
                    original_value=None,
                    adjusted_value=None,
                    explanation=message,
                    severity=RiskLevel.CRITICAL
                )
            ],
            approval_status=ApprovalStatus.REJECTED,
            risk_level=RiskLevel.CRITICAL,
            approval_threshold=ApprovalLevel.DIRECTOR,
            financial_impact=None,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=1)  # Expire immediately
        )

    def _assess_risk_and_approval(self, recommendation: PricingRecommendation) -> PricingRecommendation:
        """Assess risk level and determine approval requirements"""
        
        if not recommendation.product_info or not recommendation.recommended_price:
            recommendation.risk_level = RiskLevel.LOW
            recommendation.approval_threshold = ApprovalLevel.ANALYST
            return recommendation
        
        product = recommendation.product_info[0]
        current_price = product.current_price
        recommended_price = recommendation.recommended_price
        
        # Use the financial impact that was already calculated in revenue validation
        # If not available, fall back to simple calculation (shouldn't happen in normal flow)
        if recommendation.financial_impact:
            revenue_impact = recommendation.financial_impact.get('estimated_monthly_revenue_impact', 0)
            price_change_pct = abs(recommendation.financial_impact.get('price_change_percent', 0))  # Use abs for risk assessment
            price_change_abs = abs(recommendation.financial_impact.get('price_change_amount', 0))
        else:
            # Fallback calculation (simple, without elasticity)
            recent_sales = sum(product.hourly_sales) if product.hourly_sales else 0
            daily_sales_estimate = recent_sales * 4
            revenue_impact = (recommended_price - current_price) * daily_sales_estimate * 30
            price_change_pct = abs((recommended_price - current_price) / current_price * 100) if current_price > 0 else float('inf')
            price_change_abs = abs(recommended_price - current_price)
            
            recommendation.financial_impact = {
                "price_change_percent": (recommended_price - current_price) / current_price * 100 if current_price > 0 else 0,  # Store signed value
                "price_change_amount": recommended_price - current_price,
                "estimated_monthly_revenue_impact": revenue_impact,
                "estimated_daily_sales": daily_sales_estimate
            }

        # Determine risk level and approval threshold
        if price_change_pct >= self.guardrail_config["critical_risk_price_change"]:
            recommendation.risk_level = RiskLevel.CRITICAL
            recommendation.approval_threshold = ApprovalLevel.DIRECTOR
        elif (price_change_pct >= self.guardrail_config["high_risk_price_change"] or
              price_change_abs > self.guardrail_config["max_absolute_price_change"]):
            recommendation.risk_level = RiskLevel.HIGH
            recommendation.approval_threshold = ApprovalLevel.MANAGER
        elif (price_change_pct >= 10.0 or 
              recommendation.confidence_score < self.guardrail_config["medium_confidence_threshold"] or
              abs(revenue_impact) > 10000 or
              product.current_price > self.guardrail_config["high_value_item_threshold"]):  # $10k monthly impact
            recommendation.risk_level = RiskLevel.MEDIUM
            recommendation.approval_threshold = ApprovalLevel.SENIOR_ANALYST
        else:
            recommendation.risk_level = RiskLevel.LOW
            recommendation.approval_threshold = ApprovalLevel.ANALYST
        
        # Set expiration (recommendations expire after 7 days)
        recommendation.expires_at = datetime.now() + timedelta(days=7)
        
        return recommendation
    
    def _apply_enhanced_guardrails(self, recommendation: PricingRecommendation) -> PricingRecommendation:
        """Apply comprehensive guardrails and track violations"""
        
        violations = []
        
        # Critical check: Ensure we have valid inputs
        if not recommendation.product_info:
            return recommendation
            
        product = recommendation.product_info[0]
        original_price = recommendation.recommended_price
        
        # CRITICAL GUARDRAIL 0: Prevent zero, negative, or None prices (DANGEROUS!)
        if original_price is None or original_price <= 0:
            # This is extremely dangerous - use emergency fallback price
            emergency_price = max(
                product.current_price,  # Keep current price as safe fallback
                product.cost_price * 1.20,  # Or 20% markup on cost
                self.guardrail_config["min_absolute_price"]  # Or absolute minimum
            )
            violations.append(GuardrailViolation(
                rule_name="critical_price_protection",
                violation_type="dangerous_pricing_error",
                original_value=original_price,
                adjusted_value=emergency_price,
                explanation=f"CRITICAL: Price of ${original_price} is dangerous and has been set to emergency fallback price of ${emergency_price:.2f} to prevent business damage.",
                severity=RiskLevel.CRITICAL
            ))
            original_price = emergency_price
            
        adjusted_price = original_price
        
        # GUARDRAIL 1: Semantic price validation - detect unrealistic recommendations
        price_change_pct = abs((adjusted_price - product.current_price) / product.current_price * 100) if product.current_price > 0 else 0
        
        # If price change is extreme (>90% reduction), it's likely an error
        if adjusted_price < product.current_price * 0.1:  # More than 90% reduction
            safe_price = max(
                product.current_price * 0.5,  # Maximum 50% reduction
                product.cost_price * self.guardrail_config["price_below_cost_multiplier"],
                self.guardrail_config["min_absolute_price"]
            )
            violations.append(GuardrailViolation(
                rule_name="extreme_price_reduction_protection",
                violation_type="unrealistic_pricing",
                original_value=adjusted_price,
                adjusted_value=safe_price,
                explanation=f"Extreme price reduction detected (>{price_change_pct:.0f}% drop). Adjusted from ${adjusted_price:.2f} to ${safe_price:.2f} for safety.",
                severity=RiskLevel.CRITICAL
            ))
            adjusted_price = safe_price
        
        # GUARDRAIL 2: Prevent extremely low prices (potential fraud/error)
        min_abs_price = self.guardrail_config["min_absolute_price"]
        if adjusted_price < min_abs_price:
            violations.append(GuardrailViolation(
                rule_name="minimum_absolute_price",
                violation_type="potential_fraud_or_error",
                original_value=adjusted_price,
                adjusted_value=min_abs_price,
                explanation=f"Price adjusted from ${adjusted_price:.2f} to ${min_abs_price:.2f} to prevent potentially fraudulent or erroneous pricing.",
                severity=RiskLevel.CRITICAL
            ))
            adjusted_price = min_abs_price
        
        # GUARDRAIL 3: Price cannot be below cost + minimum margin
        min_price = product.cost_price * self.guardrail_config["price_below_cost_multiplier"]
        if adjusted_price < min_price:
            violations.append(GuardrailViolation(
                rule_name="minimum_cost_margin",
                violation_type="price_below_minimum",
                original_value=adjusted_price,
                adjusted_value=min_price,
                explanation=f"Price adjusted from ${adjusted_price:.2f} to ${min_price:.2f} to maintain minimum {(self.guardrail_config['price_below_cost_multiplier']-1)*100:.0f}% markup above cost",
                severity=RiskLevel.HIGH
            ))
            adjusted_price = min_price
        
        # GUARDRAIL 4: Maximum price change limit
        max_change = product.current_price * (self.guardrail_config["max_price_change_percent"] / 100)
        if abs(adjusted_price - product.current_price) > max_change:
            if adjusted_price > product.current_price:
                new_price = product.current_price + max_change
            else:
                new_price = product.current_price - max_change
                
            violations.append(GuardrailViolation(
                rule_name="maximum_price_change",
                violation_type="excessive_price_change",
                original_value=adjusted_price,
                adjusted_value=new_price,
                explanation=f"Price change limited to {self.guardrail_config['max_price_change_percent']:.0f}% to prevent market shock",
                severity=RiskLevel.MEDIUM
            ))
            adjusted_price = new_price
        
        # GUARDRAIL 5: Margin validation
        new_margin = ((adjusted_price - product.cost_price) / adjusted_price * 100) if adjusted_price > 0 else 0
        
        if new_margin < self.guardrail_config["min_margin_percent"]:
            min_margin_price = product.cost_price / (1 - self.guardrail_config["min_margin_percent"] / 100)
            violations.append(GuardrailViolation(
                rule_name="minimum_margin",
                violation_type="margin_too_low",
                original_value=adjusted_price,
                adjusted_value=min_margin_price,
                explanation=f"Price adjusted to maintain minimum {self.guardrail_config['min_margin_percent']:.0f}% margin",
                severity=RiskLevel.MEDIUM
            ))
            adjusted_price = min_margin_price
            
        elif new_margin > self.guardrail_config["max_margin_percent"]:
            max_margin_price = product.cost_price / (1 - self.guardrail_config["max_margin_percent"] / 100)
            violations.append(GuardrailViolation(
                rule_name="maximum_margin",
                violation_type="margin_too_high",
                original_value=adjusted_price,
                adjusted_value=max_margin_price,
                explanation=f"Price adjusted to prevent excessive {new_margin:.1f}% margin",
                severity=RiskLevel.LOW
            ))
            adjusted_price = max_margin_price
        
        # GUARDRAIL 6: Confidence-based adjustments
        if recommendation.confidence_score < self.guardrail_config["low_confidence_threshold"]:
            violations.append(GuardrailViolation(
                rule_name="low_confidence",
                violation_type="insufficient_data",
                original_value=recommendation.confidence_score,
                adjusted_value=None,
                explanation=f"Low confidence score ({recommendation.confidence_score:.2f}) - recommendation requires additional validation",
                severity=RiskLevel.MEDIUM
            ))
        
        # Update recommendation with guardrail results
        recommendation.recommended_price = adjusted_price
        recommendation.guardrail_violations = violations
        
        # Update reasoning with guardrail information
        if violations:
            guardrail_notes = "\n\nGUARDRAIL ADJUSTMENTS:\n" + "\n".join([
                f"• {v.rule_name}: {v.explanation}" for v in violations
            ])
            recommendation.reasoning += guardrail_notes
        
        return recommendation

    def submit_approval_request(self, approval_request: ApprovalRequest) -> bool:
        """Submit an approval request for a recommendation"""
        try:
            if approval_request.recommendation_id not in self.active_recommendations:
                raise ValueError("Recommendation not found")
            
            recommendation = self.active_recommendations[approval_request.recommendation_id]
            
            # Check if approver has sufficient authority
            approver_levels = {
                "analyst": ApprovalLevel.ANALYST,
                "senior_analyst": ApprovalLevel.SENIOR_ANALYST,
                "manager": ApprovalLevel.MANAGER,
                "director": ApprovalLevel.DIRECTOR
            }
            
            approver_level = approver_levels.get(approval_request.approver_role, ApprovalLevel.ANALYST)
            required_level = recommendation.approval_threshold
            
            # Check if approver has sufficient authority (enum comparison)
            if not self._has_approval_authority(approver_level, required_level):
                raise ValueError(f"Insufficient approval authority. Required: {required_level}, Has: {approver_level}")
            
            # Update recommendation status
            recommendation.approval_status = approval_request.decision
            recommendation.approval_notes = approval_request.notes
            recommendation.approved_by = approval_request.approver_id
            recommendation.approved_at = approval_request.timestamp
            
            # Store approval in history
            self.approval_history.append(approval_request)
            
            logger.info(f"Approval request processed for recommendation {approval_request.recommendation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process approval request: {e}")
            return False

    def _has_approval_authority(self, approver_level: ApprovalLevel, required_level: ApprovalLevel) -> bool:
        """Check if approver has sufficient authority"""
        level_hierarchy = {
            ApprovalLevel.ANALYST: 1,
            ApprovalLevel.SENIOR_ANALYST: 2,
            ApprovalLevel.MANAGER: 3,
            ApprovalLevel.DIRECTOR: 4
        }
        return level_hierarchy[approver_level] >= level_hierarchy[required_level]

    def get_recommendation_by_id(self, recommendation_id: str) -> Optional[PricingRecommendation]:
        """Get a recommendation by its ID"""
        return self.active_recommendations.get(recommendation_id)

    def get_pending_approvals(self, approver_role: str = None) -> List[PricingRecommendation]:
        """Get all pending approval requests, optionally filtered by approver role"""
        pending = [
            rec for rec in self.active_recommendations.values()
            if rec.approval_status == ApprovalStatus.PENDING
        ]
        
        if approver_role:
            approver_levels = {
                "analyst": ApprovalLevel.ANALYST,
                "senior_analyst": ApprovalLevel.SENIOR_ANALYST,
                "manager": ApprovalLevel.MANAGER,
                "director": ApprovalLevel.DIRECTOR
            }
            approver_level = approver_levels.get(approver_role, ApprovalLevel.ANALYST)
            pending = [
                rec for rec in pending
                if self._has_approval_authority(approver_level, rec.approval_threshold)
            ]
        
        return pending

    def _retrieve_context(self, query: PricingQuery):
        """Step 1: Retrieve relevant context from vector store or simple retriever"""
        logger.info(f"Retrieving context for query: {query.query}")
        
        # Enhance query for better retrieval
        enhanced_query = self._enhance_query(query)
        
        # Choose retrieval method
        if self.use_vector_store:
            try:
                retrieval_context = self.vector_store.search(
                    query=enhanced_query,
                    n_results=5
                )
            except Exception as e:
                logger.warning(f"Vector store search failed: {e}, falling back to simple retrieval")
                retrieval_context = self.simple_retriever.search(
                    query=enhanced_query,
                    n_results=5
                )
        else:
            retrieval_context = self.simple_retriever.search(
                query=enhanced_query,
                n_results=5
            )
        
        # If specific product IDs provided, also retrieve those
        if query.product_ids:
            for product_id in query.product_ids:
                product = self.data_loader.get_product_by_id(product_id)
                if product and product not in retrieval_context.relevant_products:
                    retrieval_context.relevant_products.append(product)
        
        logger.info(f"Retrieved {len(retrieval_context.relevant_products)} relevant products")
        return retrieval_context
    
    def _enhance_query(self, query: PricingQuery) -> str:
        """Enhance the query for better retrieval (Query Expansion technique)"""
        # Basic query expansion - add relevant pricing terms
        #pricing_terms = [
        #    "price", "pricing", "cost", "margin", "profit", "competitive", 
        #    "competitor", "sales", "inventory", "stock", "revenue"
        #]
        
        enhanced_query = query.query
        
        # Add context if provided
        if query.context:
            enhanced_query += f" Context: {query.context}"
            
        return enhanced_query
    
    def _apply_business_rules(self, products: list[ProductInfo]) -> list[ProductInfo]:
        """Step 2: Apply mathematical validation and business rules"""
        validated_products = []
        
        for product in products:
            # Calculate current margin
            current_margin = ((product.current_price - product.cost_price) / product.current_price * 100) if product.current_price > 0 else 0
            
            # Business rule validations
            validation_notes = []
            
            # Rule 1: Check if margin is below target
            if current_margin < product.target_margin_percent:
                validation_notes.append(f"Current margin ({current_margin:.1f}%) below target ({product.target_margin_percent}%)")
            
            # Rule 2: Check stock levels for pricing strategy
            if product.stock_level > 1000:
                validation_notes.append("High inventory - consider price reduction for faster turnover")
            elif product.stock_level < 50:
                validation_notes.append("Low inventory - opportunity for price increase")
            
            # Rule 3: Check price competitiveness
            if product.competitor_prices:
                avg_competitor_price = sum(product.competitor_prices) / len(product.competitor_prices)
                price_diff_pct = ((product.current_price - avg_competitor_price) / avg_competitor_price * 100) if avg_competitor_price > 0 else 0
                
                if price_diff_pct > 10:
                    validation_notes.append(f"Price {price_diff_pct:.1f}% above competitor average - risk of losing sales")
                elif price_diff_pct < -10:
                    validation_notes.append(f"Price {price_diff_pct:.1f}% below competitor average - margin opportunity")
            
            # Add validation notes to product (extend the model if needed)
            # For now, we'll include this in the reasoning
            validated_products.append(product)
        
        return validated_products

    def _generate_recommendation(self, query: PricingQuery, retrieval_context, validated_products: list[ProductInfo]) -> PricingRecommendation:
        """Step 3: Generate pricing recommendation using LLM"""
        
        if not self.llm:
            # Fallback mode without OpenAI
            return self._generate_fallback_recommendation(query, retrieval_context, validated_products)
        
        # Prepare context for LLM
        context_text = create_full_context(retrieval_context, validated_products)
        
        # Create messages
        system_message = SystemMessage(content=self._create_system_prompt())
        user_message = HumanMessage(content=self._create_user_prompt(query, context_text))
        
        # Generate response
        response = self.llm.invoke([system_message, user_message])
        
        # Parse and return structured recommendation
        return self._parse_llm_response(query, response.content, retrieval_context, validated_products)

    def _create_system_prompt(self) -> str:
        """Create system prompt for LLM"""
        return PRICING_SYSTEM_PROMPT
    
    def _create_user_prompt(self, query: PricingQuery, context_text: str) -> str:
        """Create user prompt with context and query"""
        return create_user_prompt(query, context_text)

    def _parse_llm_response(self, query: PricingQuery, response_text: str, retrieval_context, validated_products: list[ProductInfo]) -> PricingRecommendation:
        """Parse LLM response into structured recommendation"""
        
        # Extract recommended price if mentioned
        recommended_price = None
        # Simple regex to find price mentions (could be improved)
        price_matches = re.findall(r'\$([0-9]+\.?[0-9]*)', response_text)
        if price_matches:
            try:
                recommended_price = float(price_matches[-1])  # Take the last mentioned price
                
                # CRITICAL EARLY VALIDATION: Catch dangerous prices immediately
                if recommended_price <= 0:
                    logger.error(f"LLM returned dangerous price: ${recommended_price}. Using emergency fallback.")
                    # Use emergency fallback price
                    if validated_products:
                        product = validated_products[0]
                        recommended_price = max(
                            product.current_price,  # Keep current price as safe fallback
                            product.cost_price * 1.20,  # Or 20% markup on cost
                            0.50  # Or absolute minimum
                        )
                        response_text += f"\n\n[SYSTEM CORRECTION: Original price recommendation was invalid and has been corrected to ${recommended_price:.2f} for safety.]"
                    else:
                        recommended_price = None
                        
            except:
                pass
        
        # Determine confidence score based on data availability
        confidence_score = 0.8  # Default
        if len(validated_products) < 2:
            confidence_score = 0.6
        elif not any(p.competitor_prices for p in validated_products):
            confidence_score = 0.7
        
        return PricingRecommendation(
            query=query.query,
            product_info=validated_products,
            recommendation=response_text[:200] + "..." if len(response_text) > 200 else response_text,
            reasoning=response_text,
            market_context=retrieval_context.market_summary + "\n" + retrieval_context.competitor_analysis,
            confidence_score=confidence_score,
            recommended_price=recommended_price
        )

    def _generate_fallback_recommendation(self, query: PricingQuery, retrieval_context, validated_products: list[ProductInfo]) -> PricingRecommendation:
        """Generate recommendation without LLM (rule-based fallback)"""
        
        if not validated_products:
            return PricingRecommendation(
                query=query.query,
                product_info=[],
                recommendation="No relevant products found for this query.",
                reasoning="Unable to retrieve relevant product data for analysis.",
                market_context="Insufficient data available.",
                confidence_score=0.0
            )
        
        # Simple rule-based recommendation
        product = validated_products[0]  # Focus on the most relevant product
        
        # Calculate metrics
        current_margin = ((product.current_price - product.cost_price) / product.current_price * 100) if product.current_price > 0 else 0
        avg_competitor_price = sum(product.competitor_prices) / len(product.competitor_prices) if product.competitor_prices else product.current_price
        
        # Generate simple recommendation
        if current_margin < product.target_margin_percent:
            if product.stock_level < 100:  # Low stock
                recommended_price = min(avg_competitor_price * 1.05, product.current_price * 1.1)
                recommendation = f"Increase price to ${recommended_price:.2f} to improve margin (low stock supports price increase)"
            else:
                recommended_price = avg_competitor_price
                recommendation = f"Adjust price to ${recommended_price:.2f} to match competitor average while improving margin"
        else:
            if product.stock_level > 1000:  # High stock
                recommended_price = product.current_price * 0.95
                recommendation = f"Consider reducing price to ${recommended_price:.2f} to increase turnover (high inventory)"
            else:
                recommended_price = product.current_price
                recommendation = "Current pricing appears optimal - monitor competitor changes"
        
        reasoning = create_fallback_reasoning(product, current_margin, avg_competitor_price)
        
        return PricingRecommendation(
            query=query.query,
            product_info=validated_products,
            recommendation=recommendation,
            reasoning=reasoning,
            market_context=retrieval_context.market_summary,
            confidence_score=0.7,
            recommended_price=recommended_price
        )

    def get_agent_status(self) -> SystemStatus:
        """Get comprehensive status information about the agent"""
        retrieval_method = "vector_store" if self.use_vector_store else "simple_retriever"
        collection_info = self.vector_store.get_collection_info() if self.use_vector_store else self.simple_retriever.get_collection_info()
        
        # Count pending approvals and active recommendations
        pending_approvals = len([r for r in self.active_recommendations.values() if r.approval_status == ApprovalStatus.PENDING])
        active_recommendations = len(self.active_recommendations)
        
        return SystemStatus(
            initialized=self.initialized,
            has_openai_key=bool(self.openai_api_key),
            retrieval_method=retrieval_method,
            data_summary=self.data_loader.get_products_summary() if self.initialized else {},
            vector_store_info=collection_info if self.initialized else {},
            pending_approvals=pending_approvals,
            active_recommendations=active_recommendations
        )


# For backward compatibility, create an alias
PricingRAGAgent = EnhancedPricingRAGAgent 