"""
Main FastAPI Application for Iteration 1: RAG-powered Pricing Q&A System

This module provides the REST API endpoints for the pricing agent,
allowing users to submit pricing queries and receive structured recommendations.
"""
import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from src.models import PricingQuery, PricingRecommendation
from src.pricing_agent import PricingRAGAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Pricing RAG Agent - Iteration 1",
    description="AI-powered pricing analyst assistant using RAG to answer pricing queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: PricingRAGAgent = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    agent_initialized: bool


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: str


@app.on_event("startup")
async def startup_event():
    """Initialize the pricing agent on startup"""
    global agent
    try:
        logger.info("Initializing Pricing RAG Agent...")
        agent = PricingRAGAgent()
        agent.initialize()
        logger.info("Pricing RAG Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        # Don't fail startup - allow health checks to show the error


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy" if agent and agent.initialized else "not_ready",
        version="1.0.0",
        agent_initialized=agent.initialized if agent else False
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if agent and agent.initialized else "not_ready",
        version="1.0.0",
        agent_initialized=agent.initialized if agent else False
    )


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get detailed status information about the agent"""
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        status_info = agent.get_agent_status()
        return status_info
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@app.post("/query", response_model=PricingRecommendation)
async def process_pricing_query(query: PricingQuery) -> PricingRecommendation:
    """Process a pricing query and return recommendations"""
    if not agent or not agent.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        logger.info(f"Processing query: {query.query}")
        recommendation = agent.process_query(query)
        logger.info("Query processed successfully")
        return recommendation
        
    except Exception as e:
        logger.error(f"Failed to process query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@app.get("/products/summary")
async def get_products_summary() -> Dict[str, Any]:
    """Get summary information about loaded products"""
    if not agent or not agent.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        summary = agent.data_loader.get_products_summary()
        return summary
    except Exception as e:
        logger.error(f"Failed to get products summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get products summary: {str(e)}"
        )


@app.get("/products/{product_id}")
async def get_product_by_id(product_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific product"""
    if not agent or not agent.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        product = agent.data_loader.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        return product.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get product: {str(e)}"
        )


@app.get("/products/search/{search_term}")
async def search_products(search_term: str) -> Dict[str, Any]:
    """Search for products by name or brand"""
    if not agent or not agent.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        # Try both name and brand searches
        products_by_name = agent.data_loader.search_products_by_name(search_term)
        products_by_brand = agent.data_loader.get_products_by_brand(search_term)
        
        # Combine and deduplicate
        all_products = products_by_name + products_by_brand
        unique_products = []
        seen_ids = set()
        
        for product in all_products:
            if product.item_id not in seen_ids:
                unique_products.append(product)
                seen_ids.add(product.item_id)
        
        return {
            "search_term": search_term,
            "total_found": len(unique_products),
            "products": [product.dict() for product in unique_products[:10]]  # Limit to 10 results
        }
        
    except Exception as e:
        logger.error(f"Failed to search products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search products: {str(e)}"
        )


if __name__ == "__main__":
    # Run the application
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    ) 