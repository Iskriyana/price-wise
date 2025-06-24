#!/usr/bin/env python3
"""
Simple tests for the PriceWise Pricing Agent (Iteration 2)

Run this to verify that the agent is working correctly.
"""

import os
import sys

# Try to load environment variables, but don't fail if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not available, skipping .env file loading")
    pass

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from src.models import ProductInfo, CompetitorPrice, PricingRecommendation
        print("  ✅ Models imported successfully")
    except Exception as e:
        print(f"  ❌ Failed to import models: {e}")
        return False
    
    try:
        from src.tools import ProductDataRetriever, FinancialSimulationTool
        print("  ✅ Tools imported successfully")
    except Exception as e:
        print(f"  ❌ Failed to import tools: {e}")
        return False
    
    try:
        from src.pricing_agent import PricingAgent, create_pricing_agent
        print("  ✅ Pricing agent imported successfully")
    except Exception as e:
        print(f"  ❌ Failed to import pricing agent: {e}")
        return False
    
    return True

def test_agent_initialization():
    """Test agent initialization"""
    print("\n🚀 Testing agent initialization...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  OPENAI_API_KEY not set - skipping agent initialization test")
        return True
    
    try:
        from src.pricing_agent import create_pricing_agent
        agent = create_pricing_agent()
        print("  ✅ Agent initialized successfully")
        return True
    except Exception as e:
        print(f"  ❌ Failed to initialize agent: {e}")
        return False

def test_tools():
    """Test individual tools"""
    print("\n🔧 Testing tools...")
    
    try:
        from src.tools import FinancialSimulationTool, SemanticSimilarityTool
        
        # Test financial simulation tool
        sim_tool = FinancialSimulationTool()
        simulation = sim_tool._run(
            sku="TEST123",
            current_price=100.0,
            new_price=95.0,
            current_cost=50.0
        )
        print("  ✅ Financial simulation tool working")
        
        # Test semantic similarity tool
        semantic_tool = SemanticSimilarityTool()
        similarities = semantic_tool._run(
            "wireless headphones",
            ["bluetooth headphones", "wired earphones", "speakers"]
        )
        print("  ✅ Semantic similarity tool working")
        
        return True
    except Exception as e:
        print(f"  ❌ Tool test failed: {e}")
        return False

def test_models():
    """Test data models"""
    print("\n📋 Testing data models...")
    
    try:
        from src.models import ProductInfo, PricingRecommendation, FinancialSimulation
        
        # Test ProductInfo
        product = ProductInfo(
            sku="TEST123",
            name="Test Product",
            category="Test",
            current_price=100.0,
            cost=50.0,
            stock_level=100
        )
        print("  ✅ ProductInfo model working")
        
        # Test PricingRecommendation
        recommendation = PricingRecommendation(
            sku="TEST123",
            current_price=100.0,
            recommended_price=95.0,
            price_change_percent=-5.0,
            reasoning="Test reasoning",
            confidence_score=0.8
        )
        print("  ✅ PricingRecommendation model working")
        
        return True
    except Exception as e:
        print(f"  ❌ Model test failed: {e}")
        return False

def test_simple_analysis():
    """Test a simple pricing analysis (if API key is available)"""
    print("\n📊 Testing simple analysis...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  OPENAI_API_KEY not set - skipping analysis test")
        return True
    
    try:
        from src.pricing_agent import create_pricing_agent
        
        agent = create_pricing_agent()
        result = agent.run_analysis("What is the recommended price for wireless headphones?")
        
        # Check that result has expected structure
        expected_keys = ["response", "recommendations", "simulations", "conversation_history", "approval_required"]
        for key in expected_keys:
            if key not in result:
                print(f"  ❌ Missing key in result: {key}")
                return False
        
        print("  ✅ Simple analysis test passed")
        print(f"  📋 Generated {len(result['recommendations'])} recommendations")
        print(f"  💰 Generated {len(result['simulations'])} simulations")
        
        return True
    except Exception as e:
        print(f"  ❌ Analysis test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running PriceWise Agent Tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Model Test", test_models), 
        ("Tool Test", test_tools),
        ("Agent Initialization Test", test_agent_initialization),
        ("Simple Analysis Test", test_simple_analysis)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The agent is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 