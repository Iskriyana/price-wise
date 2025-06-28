"""
Prompts module for the Pricing Agent.

This module contains all prompt templates used by the Enhanced Pricing RAG Agent,
organized for better maintainability and reusability.
"""

from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional

from .models import PricingQuery, ProductInfo


# System prompt for the pricing agent LLM
PRICING_SYSTEM_PROMPT = """You are a Real-Time Pricing Analyst AI designed to support human analysts during high-velocity sales events (such as Black Friday, flash sales, promotional periods, or peak demand periods). 

**CRITICAL REVENUE MAXIMIZATION CONSTRAINT**: Your PRIMARY and MANDATORY objective is to ALWAYS maximize monthly revenue. Every single recommendation must result in a positive estimated monthly revenue impact when accounting for price elasticity effects on demand. This is non-negotiable.

**BEFORE making any price recommendation, you MUST:**
1. Calculate the expected demand change using: % demand change = price_elasticity × % price change
2. Calculate the projected revenue impact: (new_price × new_demand) - (current_price × current_demand)
3. VERIFY that the monthly revenue impact is positive
4. If the revenue impact would be negative, DO NOT recommend that price - instead suggest alternative strategies

You must consider the following inputs for each item:
- Competitor Prices: Stay competitive in a fast-moving market.
- Target Margin: Ensure prices meet or exceed the desired profit margin.
- Hourly Sales Trend: Use the last 6–12 hours of sales data to detect surges or drops in demand.
- Stock Levels: Ensure price moves help avoid stockouts or excessive leftover inventory.
- Price Elasticity: A measure of how demand is expected to change with price. Use this to simulate future demand at new price points.

Additional Instructions:
1. Estimate Total Sales for the Day: Use current hourly sales and adapt to the sales event profile. Use current hourly sales and a normalized Black Friday hourly profile (e.g., [2, 3, 5, ..., 1]) to forecast demand for the full day.

2. Simulate New Demand: Use the price_elasticity value to simulate how total demand would change if price increases or decreases by ±5% or ±10%.
   Formula: % change in demand = price_elasticity × % change in price

3. Adjust Price Based on Inventory:
   - If simulated demand exceeds stock → increase the price.
   - If simulated demand is much lower than stock → reduce the price.

4. Follow Pricing Guardrails:
   - Never recommend a price below: cost_price × (1 + target_margin_percent / 100)
   - Never recommend a price more than 10% above the highest competitor price
   - **MOST IMPORTANT**: Any recommended price change must result in a positive estimated revenue impact. A recommendation with a negative revenue impact is strictly forbidden unless there is an extreme overstock situation (more than 180 days of inventory), which you must explicitly state as the reason.
   - Never recommend to reduce price to less than $0.50

Summary of Pricing Logic:
- FIRST: Simulate demand using price elasticity and verify positive revenue impact
- If stockout risk is detected, raise the price within guardrails.
- If excess inventory is projected, lower the price within constraints, but only if revenue remains positive.
- Always justify the recommendation using data and simulation insights.
- Always show your revenue impact calculation in your reasoning.

Remember: Speed and accuracy are critical. Your top priority is to provide actionable recommendations that are mathematically guaranteed to increase revenue based on elasticity calculations.
"""


# User prompt template for pricing queries
PRICING_USER_PROMPT = PromptTemplate.from_template("""
PRICING QUERY: {query}

ADDITIONAL CONTEXT: {context}

PRODUCT DATA AND MARKET ANALYSIS:
{context_text}

REQUIRED ANALYSIS:
1. DEMAND SIMULATION: Calculate projected daily demand using hourly sales trends and price elasticity
2. INVENTORY RISK ASSESSMENT: Compare simulated demand vs. current stock levels
3. PRICE OPTIMIZATION: Recommend optimal price considering:
   - Competitor positioning (stay within 10% of highest competitor price)
   - Margin requirements (maintain minimum: cost × (1 + target_margin%))
   - Inventory balance (avoid stockouts or excess inventory)
4. SCENARIO ANALYSIS: Show impact of ±5% and ±10% price changes on demand and revenue
5. ACTIONABLE RECOMMENDATION: Provide specific price with quantified business impact

FORMAT YOUR RESPONSE WITH:
- Recommended Action: [Decrease/No Change/Increase]
- Recommended Price: $X.XX
- Expected Daily Demand: X units
- Revenue Impact: $X,XXX
- Inventory Status: [Balanced/Stockout Risk/Excess Inventory]
- Confidence Level: [High/Medium/Low]
- Reasoning: Detailed explanation with calculations
""")


class PricingAnalysisResponse(BaseModel):
    """Structured response for pricing analysis."""
    recommended_action: str = Field(description="Price action: Decrease, No Change, or Increase")
    recommended_price: float = Field(description="Specific recommended price")
    expected_daily_demand: int = Field(description="Projected daily demand in units")
    revenue_impact: float = Field(description="Expected revenue impact in dollars")
    inventory_status: str = Field(description="Inventory status: Balanced, Stockout Risk, or Excess Inventory")
    confidence_level: str = Field(description="Confidence level: High, Medium, or Low")
    reasoning: str = Field(description="Detailed explanation with calculations")


# Business rules validation prompts
MARGIN_VALIDATION_PROMPT = """
Current margin: {current_margin:.1f}%
Target margin: {target_margin}%
Status: {"✅ Above target" if current_margin >= target_margin else "⚠️ Below target"}
"""

INVENTORY_ASSESSMENT_PROMPT = """
Stock level: {stock_level} units
Daily demand estimate: {daily_demand:.0f} units
Days of inventory: {days_inventory:.1f} days
Status: {inventory_status}
"""

COMPETITOR_ANALYSIS_PROMPT = """
Current price: ${current_price:.2f}
Average competitor price: ${avg_competitor:.2f}
Price difference: {price_diff:+.1f}%
Competitive position: {competitive_status}
"""


def create_user_prompt(query: PricingQuery, context_text: str) -> str:
    """Create user prompt with context and query."""
    return PRICING_USER_PROMPT.format(
        query=query.query,
        context=query.context or "High-velocity sales event analysis",
        context_text=context_text
    )


def create_product_context(product: ProductInfo) -> str:
    """Create detailed product context for LLM analysis."""
    # Calculate metrics
    current_margin = ((product.current_price - product.cost_price) / product.current_price * 100) if product.current_price > 0 else 0
    recent_sales = sum(product.hourly_sales) if product.hourly_sales else 0
    avg_competitor_price = sum(product.competitor_prices) / len(product.competitor_prices) if product.competitor_prices else 0
    max_competitor_price = max(product.competitor_prices) if product.competitor_prices else product.current_price
    min_margin_price = product.cost_price * (1 + product.target_margin_percent / 100)
    
    # Calculate demand simulation scenarios
    price_scenarios = []
    for price_change in [-10, -5, 0, 5, 10]:
        new_price = product.current_price * (1 + price_change / 100)
        demand_change = product.price_elasticity * price_change
        new_demand_multiplier = 1 + (demand_change / 100)
        # Ensure demand doesn't go negative (minimum 5% of original demand)
        new_demand_multiplier = max(new_demand_multiplier, 0.05)
        estimated_daily_demand = recent_sales * 4 * new_demand_multiplier  # 6h to 24h extrapolation
        
        # Calculate proper revenue impact (new revenue - current revenue)
        current_daily_revenue = product.current_price * (recent_sales * 4)
        new_daily_revenue = new_price * estimated_daily_demand
        daily_revenue_impact = new_daily_revenue - current_daily_revenue
        
        price_scenarios.append(f"{price_change:+d}%: ${new_price:.2f} → {estimated_daily_demand:.0f} units/day → ${daily_revenue_impact:+,.0f} daily revenue impact")
    
    return f"""
Product: {product.item_name} (SKU: {product.item_id})

CURRENT METRICS:
- Current Price: ${product.current_price:.2f}
- Cost Price: ${product.cost_price:.2f}
- Current Margin: {current_margin:.1f}%
- Target Margin: {product.target_margin_percent}%
- Stock Level: {product.stock_level} units
- Recent Sales (6h): {recent_sales} units
- Price Elasticity: {product.price_elasticity}

COMPETITIVE LANDSCAPE:
- Avg Competitor Price: ${avg_competitor_price:.2f}
- Max Competitor Price: ${max_competitor_price:.2f}
- Individual Competitor Prices: {', '.join([f'${p:.2f}' for p in product.competitor_prices])}

PRICING CONSTRAINTS:
- Minimum Price (Margin): ${min_margin_price:.2f}
- Maximum Price (Competition): ${max_competitor_price * 1.1:.2f}

DEMAND SIMULATION SCENARIOS:
{chr(10).join(price_scenarios)}

INVENTORY ANALYSIS:
- Current Stock: {product.stock_level} units
- Estimated Daily Demand (current price): {recent_sales * 4:.0f} units
- Days of Inventory: {(product.stock_level / max(recent_sales * 4, 1)):.1f} days
"""


def create_market_summary_context(retrieval_context) -> str:
    """Create market summary context for LLM analysis."""
    context_parts = []
    
    # Add market summary
    context_parts.append("MARKET SUMMARY:")
    context_parts.append(retrieval_context.market_summary)
    context_parts.append("")
    
    # Add competitor analysis
    context_parts.append("COMPETITIVE ANALYSIS:")
    context_parts.append(retrieval_context.competitor_analysis)
    context_parts.append("")
    
    return "\n".join(context_parts)


def create_full_context(retrieval_context, validated_products: List[ProductInfo]) -> str:
    """Create full context for LLM including market summary and product details."""
    context_parts = []
    
    # Add market summary
    context_parts.append(create_market_summary_context(retrieval_context))
    
    # Add detailed product information (limit to top 3 for context window)
    context_parts.append("PRODUCT DETAILS:")
    for product in validated_products[:3]:
        context_parts.append(create_product_context(product))
    
    return "\n".join(context_parts)


# Fallback recommendation templates
FALLBACK_RECOMMENDATIONS = {
    "low_margin_low_stock": "Increase price to ${recommended_price:.2f} to improve margin (low stock supports price increase)",
    "low_margin_high_stock": "Adjust price to ${recommended_price:.2f} to match competitor average while improving margin",
    "high_margin_high_stock": "Consider reducing price to ${recommended_price:.2f} to increase turnover (high inventory)",
    "optimal": "Current pricing appears optimal - monitor competitor changes"
}


def create_fallback_reasoning(product: ProductInfo, current_margin: float, avg_competitor_price: float) -> str:
    """Create reasoning text for fallback recommendations."""
    return f"""
Analysis for {product.item_name}:
- Current margin: {current_margin:.1f}% (target: {product.target_margin_percent}%)
- Stock level: {product.stock_level} units
- Average competitor price: ${avg_competitor_price:.2f}
- Price elasticity: {product.price_elasticity}

Recommendation based on rule-based analysis of margin targets, inventory levels, and competitive positioning.
""" 