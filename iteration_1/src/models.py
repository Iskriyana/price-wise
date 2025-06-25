"""
Data models for Iteration 1: RAG-powered Pricing Q&A System

This module defines the core data structures used throughout the pricing system,
including product information, queries, recommendations, and approval workflows.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ApprovalLevel(str, Enum):
    """Approval level enumeration"""
    NONE = "none"
    ANALYST = "analyst"
    SENIOR_ANALYST = "senior_analyst"
    MANAGER = "manager"
    DIRECTOR = "director"


class ApprovalStatus(str, Enum):
    """Approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    EXPIRED = "expired"


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardrailViolation(BaseModel):
    """Model for tracking guardrail violations"""
    rule_name: str = Field(description="Name of the violated guardrail rule")
    violation_type: str = Field(description="Type of violation")
    original_value: Optional[float] = Field(default=None, description="Original recommended value")
    adjusted_value: Optional[float] = Field(default=None, description="Value after guardrail adjustment")
    explanation: str = Field(description="Explanation of why this guardrail was triggered")
    severity: RiskLevel = Field(description="Severity level of the violation")


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
    requester_id: Optional[str] = Field(default=None, description="ID of the person making the request")
    requester_role: Optional[str] = Field(default="analyst", description="Role of the requester")


class PricingRecommendation(BaseModel):
    """Pricing recommendation response model with approval workflow support"""
    query: str = Field(description="Original user query")
    product_info: List[ProductInfo] = Field(description="Relevant product information")
    recommendation: str = Field(description="Price recommendation summary")
    reasoning: str = Field(description="Detailed reasoning behind the recommendation")
    market_context: str = Field(description="Market and competitive analysis")
    confidence_score: float = Field(description="Confidence score (0-1)")
    recommended_price: Optional[float] = Field(default=None, description="Specific price recommendation")
    
    # Enhanced approval and risk management fields
    approval_threshold: ApprovalLevel = Field(default=ApprovalLevel.ANALYST, description="Required approval level")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Risk assessment")
    guardrail_violations: List[GuardrailViolation] = Field(default=[], description="List of guardrail violations")
    financial_impact: Optional[Dict[str, float]] = Field(default=None, description="Estimated financial impact")
    
    # Approval workflow fields
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING, description="Current approval status")
    approval_notes: Optional[str] = Field(default=None, description="Notes from approver")
    approved_by: Optional[str] = Field(default=None, description="ID of the approver")
    approved_at: Optional[datetime] = Field(default=None, description="Timestamp of approval")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration timestamp")
    
    # Tracking fields
    recommendation_id: Optional[str] = Field(default=None, description="Unique recommendation identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator ID")


class ApprovalRequest(BaseModel):
    """Model for approval workflow requests"""
    recommendation_id: str = Field(description="ID of the recommendation to approve/reject")
    approver_id: str = Field(description="ID of the person providing approval")
    approver_role: str = Field(description="Role of the approver")
    decision: ApprovalStatus = Field(description="Approval decision")
    notes: Optional[str] = Field(default=None, description="Approval notes")
    timestamp: datetime = Field(default_factory=datetime.now, description="Decision timestamp")


class RetrievalContext(BaseModel):
    """Context retrieved from vector database"""
    relevant_products: List[ProductInfo] = Field(description="Products matching the query")
    market_summary: str = Field(description="Summary of market conditions")
    competitor_analysis: str = Field(description="Analysis of competitor pricing")
    retrieved_chunks: List[str] = Field(description="Raw text chunks from vector search")


class SystemStatus(BaseModel):
    """System status model for monitoring"""
    initialized: bool = Field(description="Whether the agent is initialized")
    has_openai_key: bool = Field(description="Whether OpenAI API key is available")
    retrieval_method: str = Field(description="Current retrieval method being used")
    data_summary: Dict[str, Any] = Field(description="Summary of loaded data")
    vector_store_info: Dict[str, Any] = Field(description="Vector store information")
    pending_approvals: int = Field(default=0, description="Number of pending approval requests")
    active_recommendations: int = Field(default=0, description="Number of active recommendations") 