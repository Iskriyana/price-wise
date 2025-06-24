import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from src.pricing_agent import create_pricing_agent
from src.models import UserQuery

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="PriceWise - Pricing Agent API",
    description="Semi-autonomous pricing agent for retail pricing analysis",
    version="2.0.0"
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
pricing_agent = None

class PricingQuery(BaseModel):
    """Request model for pricing queries"""
    query: str
    analyst_id: Optional[str] = None
    category_permissions: Optional[list] = None

class PricingResponse(BaseModel):
    """Response model for pricing analysis"""
    success: bool
    response: str
    recommendations: list
    simulations: list
    conversation_history: list
    approval_required: bool
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the pricing agent on startup"""
    global pricing_agent
    try:
        pricing_agent = create_pricing_agent()
        print("✅ Pricing agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize pricing agent: {e}")
        raise e

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "PriceWise Pricing Agent API", 
        "version": "2.0.0",
        "status": "healthy",
        "iteration": "2 - Semi-autonomous agent with RAG, recommendations, and financial simulation"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    global pricing_agent
    
    health_status = {
        "api": "healthy",
        "agent": "healthy" if pricing_agent else "not_initialized",
        "openai_api_key": "configured" if os.getenv("OPENAI_API_KEY") else "missing"
    }
    
    overall_healthy = all(status in ["healthy", "configured"] for status in health_status.values())
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "components": health_status
    }

@app.post("/analyze", response_model=PricingResponse)
async def analyze_pricing(query: PricingQuery) -> PricingResponse:
    """
    Analyze pricing for products based on user query
    
    This endpoint runs the complete pricing analysis workflow:
    1. Query analysis
    2. Data retrieval (RAG)
    3. Recommendation generation
    4. Financial simulation
    5. Response preparation
    """
    global pricing_agent
    
    if not pricing_agent:
        raise HTTPException(status_code=500, detail="Pricing agent not initialized")
    
    try:
        # Run the pricing analysis
        result = pricing_agent.run_analysis(query.query)
        
        return PricingResponse(
            success=True,
            response=result["response"],
            recommendations=result["recommendations"],
            simulations=result["simulations"],
            conversation_history=result["conversation_history"],
            approval_required=result["approval_required"]
        )
        
    except Exception as e:
        return PricingResponse(
            success=False,
            response="",
            recommendations=[],
            simulations=[],
            conversation_history=[],
            approval_required=True,
            error=str(e)
        )

@app.get("/examples")
async def get_examples():
    """Get example queries for testing the pricing agent"""
    return {
        "examples": [
            {
                "query": "What is the recommended price for SKU12345 given that Amazon lowered their price by 10%?",
                "description": "Single product pricing analysis with competitor information"
            },
            {
                "query": "Analyze pricing for wireless headphones SKU12345 considering current stock levels",
                "description": "Product analysis with inventory considerations"
            },
            {
                "query": "Should we adjust prices for running shoes SKU67890 based on recent sales performance?",
                "description": "Sales-driven pricing analysis"
            },
            {
                "query": "Coffee maker pricing strategy - what should our price be for SKU54321?",
                "description": "General pricing strategy request"
            }
        ]
    }

@app.get("/agent-info")
async def get_agent_info():
    """Get information about the current agent configuration"""
    return {
        "iteration": 2,
        "description": "Semi-autonomous pricing agent with RAG and financial simulation",
        "features": [
            "RAG-based data retrieval",
            "Competitor price analysis",
            "Sales data integration",
            "Financial impact simulation",
            "ReAct reasoning pattern",
            "Short-term memory",
            "Human-in-the-loop approval"
        ],
        "tools": [
            "Semantic similarity matching",
            "Financial simulation",
            "Product data retrieval",
            "Sales data analysis"
        ],
        "workflow": [
            "Query analysis",
            "Data retrieval",
            "Recommendation generation",
            "Financial simulation",
            "Response preparation",
            "Approval workflow"
        ]
    }

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
        print("   Please set your OpenAI API key before running the application")
        print("   You can copy env.example to .env and add your key")
    
    print("🚀 Starting PriceWise Pricing Agent...")
    print("📊 Iteration 2: Semi-autonomous agent with RAG and financial simulation")
    print("🔧 Features: Query analysis, data retrieval, recommendations, simulations")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 