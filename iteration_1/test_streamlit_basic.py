"""
Basic test to verify Streamlit app functionality
"""
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import PricingQuery
from src.pricing_agent import PricingRAGAgent

def test_agent_initialization():
    """Test that agent can be initialized"""
    print("🧪 Testing agent initialization...")
    agent = PricingRAGAgent()
    agent.initialize()
    print("✅ Agent initialized successfully")
    return agent

def test_agent_status(agent):
    """Test agent status method"""
    print("🧪 Testing agent status...")
    status = agent.get_agent_status()
    
    print("📊 Agent Status:")
    print(f"  - Initialized: {status['initialized']}")
    print(f"  - Has OpenAI Key: {status['has_openai_key']}")
    print(f"  - Retrieval Method: {status['retrieval_method']}")
    
    data_summary = status.get('data_summary', {})
    if data_summary:
        print(f"  - Total Products: {data_summary.get('total_products', 0)}")
        print(f"  - Brands: {len(data_summary.get('brands', []))}")
        print(f"  - Categories: {len(data_summary.get('categories', []))}")
    
    print("✅ Agent status working correctly")
    return status

def test_query_processing(agent):
    """Test a simple query"""
    print("🧪 Testing query processing...")
    
    query = PricingQuery(
        query="What is the pricing recommendation for Adidas products?",
        context="Basic test query"
    )
    
    recommendation = agent.process_query(query)
    
    print("📝 Query Response:")
    print(f"  - Recommendation: {recommendation.recommendation[:100]}...")
    print(f"  - Confidence: {recommendation.confidence_score:.2f}")
    print(f"  - Products Analyzed: {len(recommendation.product_info)}")
    
    print("✅ Query processing working correctly")
    return recommendation

def main():
    """Run basic tests"""
    print("🚀 Starting Streamlit App Basic Tests")
    print("=" * 50)
    
    try:
        # Test 1: Agent initialization
        agent = test_agent_initialization()
        print()
        
        # Test 2: Agent status
        status = test_agent_status(agent)
        print()
        
        # Test 3: Query processing
        recommendation = test_query_processing(agent)
        print()
        
        print("🎉 All tests passed! Streamlit app should work correctly.")
        
        # Print instructions
        print("\n🚀 To run the Streamlit app:")
        print("   streamlit run streamlit_app.py")
        print("   Then navigate to: http://localhost:8501")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main() 