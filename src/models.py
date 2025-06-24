from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ProductInfo(BaseModel):
    """Product information model"""
    sku: str = Field(..., description="Stock Keeping Unit identifier")
    upc: Optional[str] = Field(None, description="Universal Product Code")
    gtin: Optional[str] = Field(None, description="Global Trade Item Number")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    current_price: float = Field(..., description="Current selling price")
    cost: float = Field(..., description="Product cost")
    stock_level: int = Field(..., description="Current stock level")
    
class CompetitorPrice(BaseModel):
    """Competitor pricing information"""
    competitor_name: str = Field(..., description="Name of the competitor")
    product_match_confidence: float = Field(..., description="Confidence score for product matching")
    price: float = Field(..., description="Competitor's price")
    last_updated: datetime = Field(..., description="When the price was last scraped")
    url: Optional[str] = Field(None, description="URL where price was found")

class SalesData(BaseModel):
    """Sales performance data"""
    sku: str = Field(..., description="Product SKU")
    units_sold: int = Field(..., description="Units sold in the period")
    revenue: float = Field(..., description="Total revenue")
    period_days: int = Field(..., description="Number of days in the period")
    velocity: float = Field(..., description="Sales velocity (units per day)")

class PricingRecommendation(BaseModel):
    """Pricing recommendation output"""
    sku: str = Field(..., description="Product SKU")
    current_price: float = Field(..., description="Current price")
    recommended_price: float = Field(..., description="Recommended new price")
    price_change_percent: float = Field(..., description="Percentage change in price")
    reasoning: str = Field(..., description="Explanation for the recommendation")
    confidence_score: float = Field(..., description="Confidence in the recommendation (0-1)")
    
class FinancialSimulation(BaseModel):
    """Financial impact simulation results"""
    sku: str = Field(..., description="Product SKU")
    scenario_name: str = Field(..., description="Name of the scenario")
    price_change: float = Field(..., description="Price change amount")
    estimated_demand_change: float = Field(..., description="Expected demand change percentage")
    projected_revenue_change: float = Field(..., description="Expected revenue change")
    projected_profit_change: float = Field(..., description="Expected profit change")
    break_even_volume: int = Field(..., description="Volume needed to break even")
    risk_level: str = Field(..., description="Risk assessment (Low/Medium/High)")

class AgentState(BaseModel):
    """State management for the pricing agent"""
    user_query: str = Field(..., description="Original user query")
    products_analyzed: List[ProductInfo] = Field(default_factory=list, description="Products being analyzed")
    competitor_data: List[CompetitorPrice] = Field(default_factory=list, description="Retrieved competitor data")
    sales_data: List[SalesData] = Field(default_factory=list, description="Retrieved sales data")
    recommendations: List[PricingRecommendation] = Field(default_factory=list, description="Generated recommendations")
    simulations: List[FinancialSimulation] = Field(default_factory=list, description="Financial simulations")
    conversation_history: List[str] = Field(default_factory=list, description="Conversation history for memory")
    approval_required: bool = Field(default=True, description="Whether human approval is required")
    final_response: Optional[str] = Field(None, description="Final formatted response")
    
class UserQuery(BaseModel):
    """User query input model"""
    query: str = Field(..., description="The pricing query from the analyst")
    analyst_id: Optional[str] = Field(None, description="ID of the analyst making the query")
    category_permissions: Optional[List[str]] = Field(None, description="Categories the analyst can access") 