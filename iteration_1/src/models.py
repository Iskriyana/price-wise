"""
Data models for Iteration 1: RAG-powered Pricing Q&A System

This module defines the core data structures used throughout the pricing system,
including product information, queries, and recommendations.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ProductInfo(BaseModel):
    """Product information model matching the CSV data structure"""
    item_id: str = Field(description="Unique product identifier (SKU/UPC/GTIN)")
    item_name: str = Field(description="Product name including brand")
    cost_price: float = Field(description="Cost price of the product")
    current_price: float = Field(description="Current selling price")
    competitor_prices: List[float] = Field(description="List of competitor prices")
    target_margin_percent: float = Field(description="Target profit margin percentage")
    stock_level: int = Field(description="Current inventory level")
    hourly_sales: List[int] = Field(description="Sales data for last 6 hours")
    price_elasticity: float = Field(description="Price elasticity coefficient")


class PricingQuery(BaseModel):
    """User query model for pricing questions"""
    query: str = Field(description="Natural language pricing question")
    product_ids: Optional[List[str]] = Field(default=None, description="Specific product IDs to analyze")
    context: Optional[str] = Field(default=None, description="Additional context for the query")


class PricingRecommendation(BaseModel):
    """Pricing recommendation response model"""
    query: str = Field(description="Original user query")
    product_info: List[ProductInfo] = Field(description="Relevant product information")
    recommendation: str = Field(description="Price recommendation summary")
    reasoning: str = Field(description="Detailed reasoning behind the recommendation")
    market_context: str = Field(description="Market and competitive analysis")
    confidence_score: float = Field(description="Confidence score (0-1)")
    recommended_price: Optional[float] = Field(default=None, description="Specific price recommendation")
    approval_threshold: Optional[str] = Field(default=None, description="Required approval level")
    
    
class RetrievalContext(BaseModel):
    """Context retrieved from vector database"""
    relevant_products: List[ProductInfo] = Field(description="Products matching the query")
    market_summary: str = Field(description="Summary of market conditions")
    competitor_analysis: str = Field(description="Analysis of competitor pricing")
    retrieved_chunks: List[str] = Field(description="Raw text chunks from vector search") 