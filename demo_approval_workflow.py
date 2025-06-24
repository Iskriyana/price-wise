#!/usr/bin/env python3
"""
Demo: Price Approval Workflow

This script demonstrates the complete workflow:
1. Search SKU
2. Get recommendation  
3. Show approval process
4. Save approved changes
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from src.pricing_agent import create_pricing_agent
from src.tools import ProductDataRetriever, SalesDataRetriever

load_dotenv()

def print_demo_header(title):
    """Print demo section header"""
    print("\n" + "="*80)
    print(f"🎯 DEMO: {title}")
    print("="*80)

def print_step(step_num, description):
    """Print demo step"""
    print(f"\n📋 STEP {step_num}: {description}")
    print("-" * 60)

def simulate_approval_workflow():
    """Simulate the complete approval workflow"""
    
    print_demo_header("PRICE APPROVAL WORKFLOW DEMONSTRATION")
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Demo requires OPENAI_API_KEY environment variable")
        return
    
    print_step(1, "Initialize PriceWise System")
    try:
        agent = create_pricing_agent()
        retriever = ProductDataRetriever()
        sales_retriever = SalesDataRetriever()
        print("✅ System initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Demo scenarios
    scenarios = [
        {
            "sku": "SKU12345",
            "search_query": "SKU12345",
            "scenario": "Black Friday Competitive Response",
            "context": "Amazon dropped price to $89.99, need competitive response"
        },
        {
            "sku": "SKU67890", 
            "search_query": "running shoes",
            "scenario": "Inventory Clearance",
            "context": "Overstocked with declining sales, need clearance pricing"
        }
    ]
    
    approved_changes = []
    
    for i, scenario in enumerate(scenarios, 1):
        print_demo_header(f"SCENARIO {i}: {scenario['scenario']}")
        print(f"🏪 Context: {scenario['context']}")
        
        print_step(1, "Search for Product")
        products = retriever.retrieve_product_info(scenario['search_query'])
        
        if not products:
            print(f"❌ No products found for {scenario['search_query']}")
            continue
        
        # Find the target product
        target_product = None
        for product in products:
            if product.sku == scenario['sku']:
                target_product = product
                break
        
        if not target_product:
            target_product = products[0]  # Use first match
        
        print(f"✅ Found: {target_product.name} ({target_product.sku})")
        print(f"   💰 Current Price: ${target_product.current_price:.2f}")
        print(f"   💸 Cost: ${target_product.cost:.2f}")
        print(f"   📊 Stock: {target_product.stock_level} units")
        
        # Calculate and show current margin
        margin = ((target_product.current_price - target_product.cost) / target_product.current_price) * 100
        print(f"   📈 Current Margin: {margin:.1f}%")
        
        print_step(2, "Analyze Competitors & Sales Data")
        
        # Show competitor data
        competitors = retriever.retrieve_competitor_data(target_product.sku)
        if competitors:
            print("🔍 Competitor Prices:")
            for comp in competitors:
                hours_ago = int((datetime.now() - comp.last_updated).total_seconds() / 3600)
                print(f"   🏪 {comp.competitor_name}: ${comp.price:.2f} ({hours_ago}h ago)")
        
        # Show sales data
        sales_data = sales_retriever.get_sales_data(target_product.sku, days=30)
        print(f"\n📈 Sales Performance (30 days):")
        print(f"   📦 Units Sold: {sales_data.units_sold:,}")
        print(f"   💰 Revenue: ${sales_data.revenue:,.2f}")
        print(f"   📊 Daily Velocity: {sales_data.velocity:.1f} units/day")
        
        print_step(3, "Get AI Pricing Recommendation")
        
        # Create AI query
        ai_query = f"""Analyze pricing for {target_product.name} (SKU: {target_product.sku}).
        Current price: ${target_product.current_price:.2f}, Cost: ${target_product.cost:.2f},
        Stock: {target_product.stock_level} units.
        Context: {scenario['context']}
        Please provide optimal pricing recommendation."""
        
        print("⏳ AI analyzing market conditions...")
        
        try:
            result = agent.run_analysis(ai_query)
            
            if result and result.get("recommendations"):
                rec = result["recommendations"][0]
                
                print(f"\n🎯 AI RECOMMENDATION:")
                print(f"   📊 Recommended Price: ${rec['recommended_price']:.2f}")
                
                # Calculate change
                change = rec['recommended_price'] - rec['current_price']
                change_percent = (change / rec['current_price']) * 100
                
                if change > 0:
                    direction = "📈 INCREASE"
                elif change < 0:
                    direction = "📉 DECREASE"
                else:
                    direction = "➡️ NO CHANGE"
                
                print(f"   {direction}: ${change:+.2f} ({change_percent:+.1f}%)")
                print(f"   🎯 Confidence: {rec['confidence_score']:.1%}")
                
                # Show financial simulation if available
                if result.get("simulations"):
                    sim = result["simulations"][0]
                    print(f"\n💰 Financial Impact:")
                    print(f"   📈 Revenue Change: ${sim['projected_revenue_change']:+,.2f}")
                    print(f"   💰 Profit Change: ${sim['projected_profit_change']:+,.2f}")
                    print(f"   📊 Demand Change: {sim['estimated_demand_change']:+.1f}%")
                    print(f"   ⚠️  Risk Level: {sim['risk_level']}")
                
                print_step(4, "Approval Decision Process")
                
                # Simulate approval logic
                approval_criteria = {
                    "price_change_within_limits": abs(change_percent) <= 20,  # Max 20% change
                    "confidence_adequate": rec['confidence_score'] >= 0.7,
                    "positive_profit_impact": result.get("simulations") and result["simulations"][0]['projected_profit_change'] >= 0,
                    "reasonable_risk": result.get("simulations") and result["simulations"][0]['risk_level'] in ['Low', 'Medium']
                }
                
                print("🔍 Approval Criteria Assessment:")
                for criterion, passed in approval_criteria.items():
                    status = "✅ PASS" if passed else "❌ FAIL"
                    print(f"   {status} {criterion.replace('_', ' ').title()}")
                
                # Auto-approve if all criteria met
                auto_approve = all(approval_criteria.values())
                
                if auto_approve:
                    print(f"\n✅ RECOMMENDATION APPROVED (Auto-approval)")
                    
                    # Save approved change
                    timestamp = datetime.now().isoformat()
                    change_record = {
                        "timestamp": timestamp,
                        "sku": target_product.sku,
                        "product_name": target_product.name,
                        "old_price": target_product.current_price,
                        "new_price": rec['recommended_price'],
                        "price_change": change,
                        "price_change_percent": change_percent,
                        "scenario": scenario['scenario'],
                        "context": scenario['context'],
                        "approval_method": "auto_approved",
                        "confidence": rec['confidence_score'],
                        "status": "approved_pending_implementation"
                    }
                    
                    approved_changes.append(change_record)
                    
                    print(f"   📊 Price: ${target_product.current_price:.2f} → ${rec['recommended_price']:.2f}")
                    print(f"   📁 Saved to approval queue")
                    
                else:
                    print(f"\n⚠️ RECOMMENDATION REQUIRES MANUAL REVIEW")
                    print("   📋 Reason: Failed automated approval criteria")
                    print("   👤 Escalated to senior pricing analyst")
                
            else:
                print("❌ No recommendation generated")
                
        except Exception as e:
            print(f"❌ Error getting recommendation: {e}")
        
        print(f"\n{'='*60}")
        input("⏸️  Press Enter to continue to next scenario...")
    
    # Final summary
    print_demo_header("APPROVAL SESSION SUMMARY")
    
    if approved_changes:
        # Save to file
        filename = f"demo_approved_changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(approved_changes, f, indent=2)
        
        print(f"✅ Session completed successfully")
        print(f"📊 Total recommendations processed: {len(scenarios)}")
        print(f"✅ Auto-approved changes: {len(approved_changes)}")
        print(f"📁 Results saved to: {filename}")
        
        print(f"\n📋 APPROVED CHANGES:")
        for i, change in enumerate(approved_changes, 1):
            print(f"   {i}. {change['sku']}: ${change['old_price']:.2f} → ${change['new_price']:.2f}")
            print(f"      📊 Change: ${change['price_change']:+.2f} ({change['price_change_percent']:+.1f}%)")
            print(f"      🏪 Scenario: {change['scenario']}")
        
        print(f"\n🚀 NEXT STEPS:")
        print("   1. Review approved changes in pricing system")
        print("   2. Schedule price updates for implementation")  
        print("   3. Monitor post-implementation performance")
        print("   4. Update inventory and marketing teams")
        
    else:
        print("📋 No changes approved this session")
        print("   All recommendations required manual review")
    
    print(f"\n🎯 Demo completed! This showcases the complete workflow:")
    print("   • SKU search and product analysis")
    print("   • AI-powered pricing recommendations") 
    print("   • Automated approval criteria checking")
    print("   • Change tracking and audit trail")
    print("   • Human-in-the-loop for complex decisions")

def main():
    """Run the approval workflow demo"""
    print("🎬 Starting PriceWise Approval Workflow Demo...")
    print("   This demo shows the complete pricing decision process")
    
    proceed = input("\n❓ Start demo? (y/n): ").strip().lower()
    if proceed in ['y', 'yes']:
        simulate_approval_workflow()
    else:
        print("👋 Demo cancelled")

if __name__ == "__main__":
    main() 