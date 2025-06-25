"""
RAG-powered Pricing Agent for Iteration 1

This module implements a workflow-based agent that uses Retrieval-Augmented Generation
to answer pricing questions by retrieving relevant product data and generating 
informed recommendations.
"""
import os
import logging
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from src.models import PricingQuery, PricingRecommendation, ProductInfo
from src.data_loader import PricingDataLoader
from src.vector_store import PricingVectorStore
from src.simple_retriever import SimplePricingRetriever

logger = logging.getLogger(__name__)


class PricingRAGAgent:
    """RAG-powered agent for pricing questions and recommendations"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = None
        self.data_loader = PricingDataLoader()
        self.vector_store = PricingVectorStore()
        self.simple_retriever = SimplePricingRetriever()
        self.use_vector_store = True
        self.initialized = False
        
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
            logger.info("Pricing agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize pricing agent: {e}")
            raise
    
    def process_query(self, query: PricingQuery) -> PricingRecommendation:
        """Process a pricing query using RAG workflow"""
        if not self.initialized:
            raise ValueError("Agent not initialized. Call initialize() first.")
            
        try:
            # Step 1: Retrieve relevant context
            retrieval_context = self._retrieve_context(query)
            
            # Step 2: Apply mathematical validation/threshold checks
            validated_products = self._apply_business_rules(retrieval_context.relevant_products)
            
            # Step 3: Generate recommendation using LLM
            recommendation = self._generate_recommendation(query, retrieval_context, validated_products)
            
            # Step 4: Apply guardrails and validation
            final_recommendation = self._apply_guardrails(recommendation)
            
            return final_recommendation
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise
    
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
        pricing_terms = [
            "price", "pricing", "cost", "margin", "profit", "competitive", 
            "competitor", "sales", "inventory", "stock", "revenue"
        ]
        
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
        context_text = self._prepare_context_for_llm(retrieval_context, validated_products)
        
        # Create system prompt based on best practices
        system_prompt = self._create_system_prompt()
        
        # Create user prompt with context
        user_prompt = self._create_user_prompt(query, context_text)
        
        try:
            # Generate response using LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse response into structured recommendation
            recommendation = self._parse_llm_response(query, response.content, retrieval_context, validated_products)
            
            return recommendation
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback to rule-based recommendation
            return self._generate_fallback_recommendation(query, retrieval_context, validated_products)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt following best practices"""
        return """You are an expert pricing analyst for a retail company. Your role is to analyze product pricing data and provide clear, actionable pricing recommendations.

        Guidelines:
        1. Always ground your recommendations in the provided data
        2. Consider competitor pricing, inventory levels, sales performance, and margin targets
        3. Provide specific price recommendations when possible
        4. Explain your reasoning clearly and concisely
        5. Identify approval requirements based on price change magnitude
        6. Consider business context and market conditions
        7. Suggest both conservative and aggressive pricing scenarios when relevant
        
        Response Format:
        - Start with a clear recommendation summary
        - Provide detailed reasoning with data support
        - Include market context analysis
        - Specify confidence level (high/medium/low)
        - Recommend approval threshold if price changes are significant
        
        Remember: Accuracy and actionability are paramount. If data is insufficient, state this clearly."""
    
    def _create_user_prompt(self, query: PricingQuery, context_text: str) -> str:
        """Create user prompt with context and query"""
        return f"""
        Pricing Query: {query.query}
        
        Additional Context: {query.context or "None provided"}
        
        Relevant Product Data and Market Analysis:
        {context_text}
        
        Please provide a comprehensive pricing recommendation addressing this query. Include:
        1. Specific pricing recommendation
        2. Detailed reasoning based on the data
        3. Market and competitive context
        4. Confidence assessment
        5. Any approval requirements or risk considerations
        """
    
    def _prepare_context_for_llm(self, retrieval_context, validated_products: list[ProductInfo]) -> str:
        """Prepare context text for LLM input"""
        context_parts = []
        
        # Add market summary
        context_parts.append("MARKET SUMMARY:")
        context_parts.append(retrieval_context.market_summary)
        context_parts.append("")
        
        # Add competitor analysis
        context_parts.append("COMPETITIVE ANALYSIS:")
        context_parts.append(retrieval_context.competitor_analysis)
        context_parts.append("")
        
        # Add detailed product information
        context_parts.append("PRODUCT DETAILS:")
        for product in validated_products[:3]:  # Limit to top 3 for context window
            # Calculate metrics
            current_margin = ((product.current_price - product.cost_price) / product.current_price * 100) if product.current_price > 0 else 0
            recent_sales = sum(product.hourly_sales) if product.hourly_sales else 0
            avg_competitor_price = sum(product.competitor_prices) / len(product.competitor_prices) if product.competitor_prices else 0
            
            product_text = f"""
            Product: {product.item_name} (SKU: {product.item_id})
            - Current Price: ${product.current_price:.2f}
            - Cost Price: ${product.cost_price:.2f}
            - Current Margin: {current_margin:.1f}%
            - Target Margin: {product.target_margin_percent}%
            - Stock Level: {product.stock_level} units
            - Recent Sales (6h): {recent_sales} units
            - Price Elasticity: {product.price_elasticity}
            - Avg Competitor Price: ${avg_competitor_price:.2f}
            - Individual Competitor Prices: {', '.join([f'${p:.2f}' for p in product.competitor_prices])}
            """
            context_parts.append(product_text)
        
        return "\n".join(context_parts)
    
    def _parse_llm_response(self, query: PricingQuery, response_text: str, retrieval_context, validated_products: list[ProductInfo]) -> PricingRecommendation:
        """Parse LLM response into structured recommendation"""
        
        # Extract recommended price if mentioned
        recommended_price = None
        # Simple regex to find price mentions (could be improved)
        import re
        price_matches = re.findall(r'\$([0-9]+\.?[0-9]*)', response_text)
        if price_matches:
            try:
                recommended_price = float(price_matches[-1])  # Take the last mentioned price
            except:
                pass
        
        # Determine confidence score based on data availability
        confidence_score = 0.8  # Default
        if len(validated_products) < 2:
            confidence_score = 0.6
        elif not any(p.competitor_prices for p in validated_products):
            confidence_score = 0.7
        
        # Determine approval threshold
        approval_threshold = "analyst"  # Default
        if recommended_price and validated_products:
            price_change_pct = abs((recommended_price - validated_products[0].current_price) / validated_products[0].current_price * 100)
            if price_change_pct > 20:
                approval_threshold = "manager"
            elif price_change_pct > 10:
                approval_threshold = "senior_analyst"
        
        return PricingRecommendation(
            query=query.query,
            product_info=validated_products,
            recommendation=response_text[:200] + "..." if len(response_text) > 200 else response_text,
            reasoning=response_text,
            market_context=retrieval_context.market_summary + "\n" + retrieval_context.competitor_analysis,
            confidence_score=confidence_score,
            recommended_price=recommended_price,
            approval_threshold=approval_threshold
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
        
        reasoning = f"""
        Analysis for {product.item_name}:
        - Current margin: {current_margin:.1f}% (target: {product.target_margin_percent}%)
        - Stock level: {product.stock_level} units
        - Average competitor price: ${avg_competitor_price:.2f}
        - Current price competitiveness: {'good' if abs(product.current_price - avg_competitor_price) < avg_competitor_price * 0.1 else 'needs adjustment'}
        """
        
        return PricingRecommendation(
            query=query.query,
            product_info=validated_products,
            recommendation=recommendation,
            reasoning=reasoning,
            market_context=retrieval_context.market_summary,
            confidence_score=0.7,
            recommended_price=recommended_price,
            approval_threshold="analyst"
        )
    
    def _apply_guardrails(self, recommendation: PricingRecommendation) -> PricingRecommendation:
        """Step 4: Apply guardrails and final validation"""
        
        # Guardrail 1: Check for unreasonable price recommendations
        if recommendation.recommended_price and recommendation.product_info:
            product = recommendation.product_info[0]
            
            # Don't recommend prices below cost
            if recommendation.recommended_price < product.cost_price:
                recommendation.recommended_price = product.cost_price * 1.1  # 10% markup minimum
                recommendation.reasoning += "\n[GUARDRAIL] Adjusted price to maintain minimum 10% markup above cost."
            
            # Don't recommend extreme price changes (>50%)
            max_change = product.current_price * 0.5
            if abs(recommendation.recommended_price - product.current_price) > max_change:
                if recommendation.recommended_price > product.current_price:
                    recommendation.recommended_price = product.current_price + max_change
                else:
                    recommendation.recommended_price = product.current_price - max_change
                recommendation.reasoning += "\n[GUARDRAIL] Limited price change to 50% to reduce market shock."
                recommendation.approval_threshold = "manager"
        
        # Guardrail 2: Ensure factual consistency
        if recommendation.confidence_score < 0.5:
            recommendation.reasoning += "\n[GUARDRAIL] Low confidence recommendation - requires additional validation."
            recommendation.approval_threshold = "manager"
        
        return recommendation
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status information about the agent"""
        retrieval_method = "vector_store" if self.use_vector_store else "simple_retriever"
        collection_info = self.vector_store.get_collection_info() if self.use_vector_store else self.simple_retriever.get_collection_info()
        
        status = {
            "initialized": self.initialized,
            "has_openai_key": bool(self.openai_api_key),
            "retrieval_method": retrieval_method,
            "data_summary": self.data_loader.get_products_summary() if self.initialized else {},
            "vector_store_info": collection_info if self.initialized else {}
        }
        return status 