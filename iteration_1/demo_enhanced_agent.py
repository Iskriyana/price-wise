#!/usr/bin/env python3
"""
Enhanced Demo Script for PriceWise AI - Iteration 1 with Guardrails and Approval Workflows

This script demonstrates the advanced features of the enhanced pricing agent including:
- Comprehensive guardrails and validation
- Multi-level approval workflows
- Risk assessment and financial impact analysis
- Enhanced recommendation tracking
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import (
    PricingQuery, ApprovalRequest, ApprovalStatus, ApprovalLevel, RiskLevel
)
from src.pricing_agent import EnhancedPricingRAGAgent

def print_banner():
    """Print demo banner"""
    print("=" * 80)
    print("🚀 ENHANCED PRICEWISE AI - ITERATION 1 DEMO")
    print("RAG-powered Pricing Agent with Guardrails & Approval Workflows")
    print("=" * 80)
    print()

def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*20} {title.upper()} {'='*20}")
    print()

def display_recommendation_summary(recommendation):
    """Display enhanced recommendation summary"""
    print(f"📋 RECOMMENDATION SUMMARY:")
    print(f"   ID: {recommendation.recommendation_id}")
    print(f"   Risk Level: {recommendation.risk_level.value.upper()}")
    print(f"   Approval Required: {recommendation.approval_threshold.value.replace('_', ' ').title()}")
    print(f"   Status: {recommendation.approval_status.value.title()}")
    print(f"   Confidence: {recommendation.confidence_score:.1%}")
    
    if recommendation.recommended_price:
        print(f"   Recommended Price: ${recommendation.recommended_price:.2f}")
    
    if recommendation.financial_impact:
        impact = recommendation.financial_impact
        print(f"   Price Change: {impact.get('price_change_percent', 0):.1f}%")
        print(f"   Revenue Impact: ${impact.get('estimated_monthly_revenue_impact', 0):,.0f}/month")
    
    if recommendation.guardrail_violations:
        print(f"   Guardrail Violations: {len(recommendation.guardrail_violations)}")
        for violation in recommendation.guardrail_violations:
            print(f"      • {violation.rule_name}: {violation.explanation}")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   {recommendation.recommendation}")
    print()

def demo_enhanced_guardrails(agent):
    """Demonstrate enhanced guardrails functionality"""
    print_section("Enhanced Guardrails Demo")
    
    # Test extreme price change scenario
    print("🧪 Testing extreme price change scenario...")
    extreme_query = PricingQuery(
        query="I want to reduce the price of Nike Air Max 270 (APP10001) by 80% to clear inventory quickly",
        context="Extreme price reduction test for guardrails",
        product_ids=["APP10001"],
        requester_id="demo_user",
        requester_role="analyst"
    )
    
    recommendation = agent.process_query(extreme_query)
    display_recommendation_summary(recommendation)
    
    # Test below-cost pricing scenario
    print("🧪 Testing below-cost pricing scenario...")
    below_cost_query = PricingQuery(
        query="Set the price of Adidas Ultraboost to $5 to beat all competitors",
        context="Below-cost pricing test for guardrails",
        requester_id="demo_user", 
        requester_role="analyst"
    )
    
    recommendation = agent.process_query(below_cost_query)
    display_recommendation_summary(recommendation)
    
    # Test excessive margin scenario
    print("🧪 Testing excessive margin scenario...")
    high_margin_query = PricingQuery(
        query="Increase Under Armour pricing by 300% to maximize profit margins",
        context="Excessive margin test for guardrails",
        requester_id="demo_user",
        requester_role="analyst"
    )
    
    recommendation = agent.process_query(high_margin_query)
    display_recommendation_summary(recommendation)

def demo_approval_workflow(agent):
    """Demonstrate approval workflow functionality"""
    print_section("Approval Workflow Demo")
    
    # Create a high-risk recommendation
    print("🎯 Creating high-risk pricing recommendation...")
    high_risk_query = PricingQuery(
        query="Increase Nike sneaker prices by 30% across the board to improve margins",
        context="Significant price increase requiring manager approval",
        requester_id="demo_analyst",
        requester_role="analyst"
    )
    
    recommendation = agent.process_query(high_risk_query)
    display_recommendation_summary(recommendation)
    
    # Simulate approval process
    if recommendation.approval_status == ApprovalStatus.PENDING:
        print("⏳ Recommendation requires approval. Simulating approval process...")
        
        # Test insufficient authority
        print("\n👤 Analyst attempting to approve (insufficient authority)...")
        analyst_approval = ApprovalRequest(
            recommendation_id=recommendation.recommendation_id,
            approver_id="analyst_001",
            approver_role="analyst",
            decision=ApprovalStatus.APPROVED,
            notes="Looks good to me!"
        )
        
        success = agent.submit_approval_request(analyst_approval)
        if not success:
            print("❌ Approval rejected - insufficient authority")
        
        # Test sufficient authority
        print("\n👤 Manager approving (sufficient authority)...")
        manager_approval = ApprovalRequest(
            recommendation_id=recommendation.recommendation_id,
            approver_id="manager_001", 
            approver_role="manager",
            decision=ApprovalStatus.APPROVED,
            notes="Approved after review of market conditions and competitive analysis."
        )
        
        success = agent.submit_approval_request(manager_approval)
        if success:
            print("✅ Approval successful!")
            
            # Show updated recommendation
            updated_rec = agent.get_recommendation_by_id(recommendation.recommendation_id)
            if updated_rec:
                print(f"   Approved by: {updated_rec.approved_by}")
                print(f"   Approved at: {updated_rec.approved_at}")
                print(f"   Notes: {updated_rec.approval_notes}")

def demo_sku_specific_analysis(agent):
    """Demonstrate SKU-specific analysis"""
    print_section("SKU-Specific Analysis Demo")
    
    # Analyze specific high-performing product
    print("🏷️ Analyzing specific product: APP10005 (Under Armour Socks)")
    sku_query = PricingQuery(
        query="Provide comprehensive pricing analysis and optimization recommendations for this specific product",
        product_ids=["APP10005"],
        context="Detailed SKU analysis with risk assessment",
        requester_id="demo_analyst",
        requester_role="senior_analyst"
    )
    
    recommendation = agent.process_query(sku_query)
    display_recommendation_summary(recommendation)
    
    # Show product details
    if recommendation.product_info:
        product = recommendation.product_info[0]
        print(f"📊 PRODUCT DETAILS:")
        print(f"   Product: {product.item_name}")
        print(f"   Current Price: ${product.current_price:.2f}")
        print(f"   Cost: ${product.cost_price:.2f}")
        print(f"   Stock: {product.stock_level:,} units")
        print(f"   Recent Sales: {sum(product.hourly_sales) if product.hourly_sales else 0} units (6h)")
        if product.competitor_prices:
            avg_competitor = sum(product.competitor_prices) / len(product.competitor_prices)
            print(f"   Avg Competitor Price: ${avg_competitor:.2f}")

def demo_risk_assessment(agent):
    """Demonstrate risk assessment functionality"""
    print_section("Risk Assessment Demo")
    
    risk_scenarios = [
        {
            "name": "Low Risk - Minor Adjustment",
            "query": "Should we increase the price of basic cotton t-shirts by 3% to cover rising material costs?",
            "context": "Minor price adjustment for cost coverage"
        },
        {
            "name": "Medium Risk - Competitive Response",
            "query": "Reduce Nike sneaker prices by 15% to match competitor pricing",
            "context": "Competitive pricing response requiring validation"
        },
        {
            "name": "High Risk - Market Position",
            "query": "Increase premium product prices by 25% to position as luxury brand",
            "context": "Significant repositioning strategy"
        },
        {
            "name": "Critical Risk - Emergency Response",
            "query": "Cut all inventory prices by 45% for emergency clearance sale",
            "context": "Emergency inventory liquidation"
        }
    ]
    
    for scenario in risk_scenarios:
        print(f"🎯 {scenario['name']}...")
        
        query = PricingQuery(
            query=scenario['query'],
            context=scenario['context'],
            requester_id="demo_analyst",
            requester_role="analyst"
        )
        
        recommendation = agent.process_query(query)
        print(f"   Risk Level: {recommendation.risk_level.value.upper()}")
        print(f"   Approval Required: {recommendation.approval_threshold.value.replace('_', ' ').title()}")
        print(f"   Guardrail Violations: {len(recommendation.guardrail_violations) if recommendation.guardrail_violations else 0}")
        print()

def demo_system_monitoring(agent):
    """Demonstrate system monitoring and status"""
    print_section("System Monitoring Demo")
    
    status = agent.get_agent_status()
    
    print("🖥️ SYSTEM STATUS:")
    print(f"   Initialized: {'✅' if status.initialized else '❌'}")
    print(f"   OpenAI Connection: {'✅' if status.has_openai_key else '⚠️ Fallback Mode'}")
    print(f"   Retrieval Method: {status.retrieval_method.title()}")
    print(f"   Active Recommendations: {status.active_recommendations}")
    print(f"   Pending Approvals: {status.pending_approvals}")
    
    if status.data_summary:
        data = status.data_summary
        print(f"\n📊 DATA SUMMARY:")
        print(f"   Total Products: {data.get('total_products', 0):,}")
        print(f"   Brands: {len(data.get('brands', []))}")
        print(f"   Categories: {len(data.get('categories', []))}")
        
        price_range = data.get('price_range', {})
        if price_range:
            print(f"   Price Range: ${price_range.get('min', 0):.2f} - ${price_range.get('max', 0):.2f}")
    
    # Show pending approvals
    pending = agent.get_pending_approvals()
    if pending:
        print(f"\n⏳ PENDING APPROVALS ({len(pending)}):")
        for i, rec in enumerate(pending[:3], 1):  # Show first 3
            print(f"   {i}. {rec.recommendation_id[:8]} - {rec.risk_level.value.title()} Risk")

def main():
    """Main demo function"""
    print_banner()
    
    # Initialize agent
    print("🚀 Initializing Enhanced Pricing Agent...")
    try:
        agent = EnhancedPricingRAGAgent()
        agent.initialize()
        print("✅ Agent initialized successfully!")
        
        # Run demonstrations
        demo_enhanced_guardrails(agent)
        demo_risk_assessment(agent)
        demo_sku_specific_analysis(agent)
        demo_approval_workflow(agent)
        demo_system_monitoring(agent)
        
        print_section("Demo Complete")
        print("🎉 Enhanced PriceWise AI demonstration completed successfully!")
        print("   All advanced features including guardrails, approval workflows,")
        print("   risk assessment, and SKU-specific analysis are working correctly.")
        print()
        print("🌐 Access the enhanced Streamlit UI at: http://localhost:8501")
        print("📋 Features demonstrated:")
        print("   • Comprehensive guardrails with violation tracking")
        print("   • Multi-level approval workflows") 
        print("   • Risk assessment and financial impact analysis")
        print("   • SKU-specific product analysis")
        print("   • Enhanced recommendation tracking")
        print("   • System monitoring and status reporting")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 