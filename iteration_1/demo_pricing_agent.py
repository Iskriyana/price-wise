"""
Demo script for Iteration 1: RAG-powered Pricing Agent

This script demonstrates the pricing agent's capabilities with example queries
that showcase the key features outlined in the project requirements.
"""
import os
import logging
from typing import List
from dotenv import load_dotenv
from src.models import PricingQuery
from src.pricing_agent import PricingRAGAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_demo_queries(agent: PricingRAGAgent) -> None:
    """Run a series of demo queries to showcase agent capabilities"""
    
    # Demo queries based on project requirements
    demo_queries = [
        PricingQuery(
            query="What is the recommended price for Product SKU APP10000 given that our main competitor lowered their price by 10% yesterday?",
            product_ids=["APP10000"],
            context="Competitor price reduction scenario"
        ),
        PricingQuery(
            query="Should we increase prices for Adidas T-shirts to improve our profit margin?",
            context="Margin optimization for brand category"
        ),
        PricingQuery(
            query="Which Nike products are overpriced compared to competitors?",
            context="Competitive pricing analysis"
        ),
        PricingQuery(
            query="What pricing strategy should we use for products with high inventory levels?",
            context="Inventory management pricing"
        ),
        PricingQuery(
            query="Recommend pricing for Under Armour Socks (APP10005) considering current market conditions",
            product_ids=["APP10005"],
            context="Market-based pricing recommendation"
        )
    ]
    
    print("=" * 80)
    print("ITERATION 1: RAG-POWERED PRICING AGENT DEMO")
    print("=" * 80)
    print()
    
    for i, query in enumerate(demo_queries, 1):
        print(f"DEMO QUERY {i}:")
        print(f"Question: {query.query}")
        if query.context:
            print(f"Context: {query.context}")
        if query.product_ids:
            print(f"Specific Products: {', '.join(query.product_ids)}")
        print("-" * 80)
        
        try:
            # Process the query
            recommendation = agent.process_query(query)
            
            # Display results
            print("📊 RECOMMENDATION:")
            print(f"   {recommendation.recommendation}")
            print()
            
            if recommendation.recommended_price:
                print(f"💰 SUGGESTED PRICE: ${recommendation.recommended_price:.2f}")
                print()
            
            print("🧠 REASONING:")
            # Display first few lines of reasoning
            reasoning_lines = recommendation.reasoning.split('\n')[:5]
            for line in reasoning_lines:
                if line.strip():
                    print(f"   {line.strip()}")
            if len(recommendation.reasoning.split('\n')) > 5:
                print("   ...")
            print()
            
            print("📈 MARKET CONTEXT:")
            context_lines = recommendation.market_context.split('\n')[:3]
            for line in context_lines:
                if line.strip():
                    print(f"   {line.strip()}")
            print()
            
            print(f"🎯 CONFIDENCE: {recommendation.confidence_score:.1%}")
            if recommendation.approval_threshold:
                print(f"✅ APPROVAL REQUIRED: {recommendation.approval_threshold}")
            
            print()
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            print()
        
        print("=" * 80)
        print()


def display_system_status(agent: PricingRAGAgent) -> None:
    """Display system status and capabilities"""
    status = agent.get_agent_status()
    
    print("🖥️  SYSTEM STATUS:")
    print(f"   Agent Initialized: {'✅' if status['initialized'] else '❌'}")
    print(f"   OpenAI Integration: {'✅' if status['has_openai_key'] else '❌ (Fallback mode)'}")
    print()
    
    if status['data_summary']:
        data_summary = status['data_summary']
        print("📦 DATA SUMMARY:")
        print(f"   Total Products: {data_summary['total_products']}")
        print(f"   Brands: {len(data_summary['brands'])} ({', '.join(data_summary['brands'][:5])}{'...' if len(data_summary['brands']) > 5 else ''})")
        print(f"   Categories: {len(data_summary['categories'])} ({', '.join(data_summary['categories'][:5])}{'...' if len(data_summary['categories']) > 5 else ''})")
        print(f"   Price Range: ${data_summary['price_range']['min']:.2f} - ${data_summary['price_range']['max']:.2f}")
        print(f"   Average Price: ${data_summary['price_range']['avg']:.2f}")
        print()
    
    if status['vector_store_info']:
        vs_info = status['vector_store_info']
        print("🔍 VECTOR STORE:")
        print(f"   Collection: {vs_info.get('name', 'N/A')}")
        print(f"   Documents: {vs_info.get('count', 0)}")
        print()


def main():
    """Main demo function"""
    print("Initializing Pricing RAG Agent...")
    
    try:
        # Initialize the agent
        agent = PricingRAGAgent()
        agent.initialize()
        
        # Display system status
        display_system_status(agent)
        
        # Run demo queries
        run_demo_queries(agent)
        
        print("✅ Demo completed successfully!")
        print()
        print("To run the web API:")
        print("   streamlit run streamlit_app.py")
        print()
        print("To test specific queries:")
        print("   curl -X POST http://localhost:8000/query \\")
        print('        -H "Content-Type: application/json" \\')
        print('        -d \'{"query": "Your pricing question here"}\'')
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
        print()
        print("Troubleshooting:")
        print("1. Ensure data/apparel_pricing_data.csv exists")
        print("2. Check if OPENAI_API_KEY is set (optional - fallback mode available)")
        print("3. Verify all dependencies are installed: pip install -r requirements.txt")


if __name__ == "__main__":
    main() 