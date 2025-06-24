#!/usr/bin/env python3
"""
Interactive Pricing System with SKU Search and Approval Workflow

This script provides a user-friendly interface for pricing analysts to:
1. Search for products by SKU or name
2. Get AI-powered pricing recommendations
3. Approve/reject recommendations
4. Track approved price changes in a file
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from src.pricing_agent import create_pricing_agent
from src.tools import ProductDataRetriever, SalesDataRetriever

# Load environment variables
load_dotenv()

# File to store approved price changes
APPROVED_CHANGES_FILE = "approved_price_changes.json"
PRICE_CHANGE_LOG_CSV = "price_change_log.csv"

def print_header():
    """Print the application header"""
    print("\n" + "="*80)
    print("🎯 PRICEWISE - INTERACTIVE PRICING SYSTEM")
    print("="*80)
    print("💡 Search SKUs • Get Recommendations • Approve Changes")
    print("-"*80)

def print_separator(title="", char="-", width=60):
    """Print a separator with optional title"""
    if title:
        print(f"\n{char*width}")
        print(f"  {title}")
        print(f"{char*width}")
    else:
        print(f"{char*width}")

def search_products(query: str, retriever: ProductDataRetriever) -> List[Dict]:
    """Search for products by SKU or name"""
    products = retriever.retrieve_product_info(query)
    
    if not products:
        print(f"❌ No products found for: '{query}'")
        return []
    
    print(f"🔍 Found {len(products)} product(s):")
    print_separator()
    
    product_list = []
    for i, product in enumerate(products, 1):
        print(f"  {i}. 🏷️  SKU: {product.sku}")
        print(f"     📦 Name: {product.name}")
        print(f"     🏪 Category: {product.category}")
        print(f"     💰 Current Price: ${product.current_price:.2f}")
        print(f"     📊 Stock: {product.stock_level} units")
        print(f"     💸 Cost: ${product.cost:.2f}")
        
        # Calculate current margin
        margin = ((product.current_price - product.cost) / product.current_price) * 100
        margin_emoji = "🟢" if margin > 40 else "🟡" if margin > 20 else "🔴"
        print(f"     {margin_emoji} Margin: {margin:.1f}%")
        print()
        
        product_list.append({
            'index': i,
            'product': product,
            'margin': margin
        })
    
    return product_list

def display_competitor_analysis(sku: str, retriever: ProductDataRetriever):
    """Display competitor pricing analysis"""
    competitors = retriever.retrieve_competitor_data(sku)
    
    if not competitors:
        print("⚠️  No competitor data available")
        return
    
    print_separator("🔍 COMPETITOR ANALYSIS")
    
    for comp in competitors:
        hours_ago = int((datetime.now() - comp.last_updated).total_seconds() / 3600)
        confidence_emoji = "🟢" if comp.product_match_confidence > 0.9 else "🟡" if comp.product_match_confidence > 0.8 else "🔴"
        
        print(f"  🏪 {comp.competitor_name}")
        print(f"     💰 Price: ${comp.price:.2f}")
        print(f"     {confidence_emoji} Match Confidence: {comp.product_match_confidence:.1%}")
        print(f"     🕐 Updated: {hours_ago}h ago")
        print()

def display_sales_performance(sku: str, sales_retriever: SalesDataRetriever):
    """Display sales performance data"""
    sales_data = sales_retriever.get_sales_data(sku, days=30)
    
    print_separator("📈 SALES PERFORMANCE (30 DAYS)")
    
    print(f"  📦 Units Sold: {sales_data.units_sold:,}")
    print(f"  💰 Revenue: ${sales_data.revenue:,.2f}")
    print(f"  📊 Daily Velocity: {sales_data.velocity:.1f} units/day")
    
    # Performance indicators
    if sales_data.velocity > 20:
        performance = "🚀 High Performer"
    elif sales_data.velocity > 10:
        performance = "📈 Good Performer"
    elif sales_data.velocity > 5:
        performance = "📊 Average Performer"
    else:
        performance = "🔻 Slow Mover"
    
    print(f"  {performance}")
    print()

def get_pricing_recommendation(sku: str, query: str, agent):
    """Get AI pricing recommendation for a SKU"""
    print_separator("🤖 AI ANALYSIS IN PROGRESS", "=")
    print("⏳ Analyzing market conditions...")
    print("⏳ Running financial simulations...")
    print("⏳ Generating recommendations...")
    
    try:
        result = agent.run_analysis(query)
        return result
    except Exception as e:
        print(f"❌ Error getting recommendation: {e}")
        return None

def display_recommendation(result: Dict[str, Any]):
    """Display the pricing recommendation with enhanced formatting"""
    if not result:
        return False
    
    print_separator("🎯 AI PRICING RECOMMENDATION", "=")
    
    # Display recommendations
    if result.get("recommendations"):
        for i, rec in enumerate(result["recommendations"], 1):
            print(f"\n📊 RECOMMENDATION {i}:")
            print(f"   🏷️  SKU: {rec['sku']}")
            print(f"   💰 Current Price: ${rec['current_price']:.2f}")
            print(f"   🎯 Recommended Price: ${rec['recommended_price']:.2f}")
            
            # Price change calculation
            change = rec['recommended_price'] - rec['current_price']
            change_percent = (change / rec['current_price']) * 100
            
            if change > 0:
                direction = "📈 INCREASE"
                color = "🟢"
            elif change < 0:
                direction = "📉 DECREASE" 
                color = "🔴"
            else:
                direction = "➡️ NO CHANGE"
                color = "🟡"
            
            print(f"   {color} {direction}: ${change:+.2f} ({change_percent:+.1f}%)")
            
            # Confidence score
            confidence = rec['confidence_score']
            conf_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
            print(f"   {conf_emoji} Confidence: {confidence:.1%}")
    
    # Display financial simulation
    if result.get("simulations"):
        print_separator("💰 FINANCIAL IMPACT SIMULATION")
        
        for sim in result["simulations"]:
            print(f"   📈 Revenue Impact: ${sim['projected_revenue_change']:+,.2f}")
            print(f"   💰 Profit Impact: ${sim['projected_profit_change']:+,.2f}")
            print(f"   📊 Demand Change: {sim['estimated_demand_change']:+.1f}%")
            
            risk_colors = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
            print(f"   {risk_colors.get(sim['risk_level'], '⚪')} Risk Level: {sim['risk_level']}")
    
    return True

def save_approved_change(sku: str, old_price: float, new_price: float, 
                        recommendation_data: Dict, user_notes: str = ""):
    """Save approved price change to files"""
    timestamp = datetime.now().isoformat()
    
    # Save to JSON file (detailed data)
    change_record = {
        "timestamp": timestamp,
        "sku": sku,
        "old_price": old_price,
        "new_price": new_price,
        "price_change": new_price - old_price,
        "price_change_percent": ((new_price - old_price) / old_price) * 100,
        "user_notes": user_notes,
        "recommendation_data": recommendation_data,
        "status": "approved_pending_implementation"
    }
    
    # Load existing data
    approved_changes = []
    if os.path.exists(APPROVED_CHANGES_FILE):
        try:
            with open(APPROVED_CHANGES_FILE, 'r') as f:
                approved_changes = json.load(f)
        except:
            approved_changes = []
    
    # Add new change
    approved_changes.append(change_record)
    
    # Save back to JSON
    with open(APPROVED_CHANGES_FILE, 'w') as f:
        json.dump(approved_changes, f, indent=2)
    
    # Save to CSV log (for easy viewing)
    csv_exists = os.path.exists(PRICE_CHANGE_LOG_CSV)
    with open(PRICE_CHANGE_LOG_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if file is new
        if not csv_exists:
            writer.writerow(['Timestamp', 'SKU', 'Old_Price', 'New_Price', 
                           'Change_Amount', 'Change_Percent', 'User_Notes', 'Status'])
        
        writer.writerow([
            timestamp,
            sku,
            f"${old_price:.2f}",
            f"${new_price:.2f}",
            f"${new_price - old_price:+.2f}",
            f"{((new_price - old_price) / old_price) * 100:+.1f}%",
            user_notes,
            "approved_pending_implementation"
        ])
    
    print(f"✅ Price change saved to {APPROVED_CHANGES_FILE} and {PRICE_CHANGE_LOG_CSV}")

def view_approved_changes():
    """View recently approved price changes"""
    if not os.path.exists(APPROVED_CHANGES_FILE):
        print("📄 No approved price changes found.")
        return
    
    try:
        with open(APPROVED_CHANGES_FILE, 'r') as f:
            changes = json.load(f)
        
        if not changes:
            print("📄 No approved price changes found.")
            return
        
        print_separator("📋 RECENTLY APPROVED PRICE CHANGES", "=")
        
        # Show last 10 changes
        recent_changes = changes[-10:]
        
        for i, change in enumerate(recent_changes, 1):
            timestamp = datetime.fromisoformat(change['timestamp'])
            print(f"\n{i}. 🏷️  SKU: {change['sku']}")
            print(f"   💰 Price Change: ${change['old_price']:.2f} → ${change['new_price']:.2f}")
            print(f"   📊 Change: ${change['price_change']:+.2f} ({change['price_change_percent']:+.1f}%)")
            print(f"   🕐 Approved: {timestamp.strftime('%Y-%m-%d %H:%M')}")
            if change.get('user_notes'):
                print(f"   📝 Notes: {change['user_notes']}")
            print(f"   📋 Status: {change['status']}")
        
        print(f"\n📊 Total approved changes: {len(changes)}")
        
    except Exception as e:
        print(f"❌ Error reading approved changes: {e}")

def main():
    """Main interactive pricing application"""
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Please create a .env file with: OPENAI_API_KEY=your_key_here")
        return
    
    # Initialize system
    print("🚀 Initializing PriceWise Interactive System...")
    
    try:
        agent = create_pricing_agent()
        retriever = ProductDataRetriever()
        sales_retriever = SalesDataRetriever()
        print("✅ System ready!")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Main application loop
    while True:
        print_header()
        print("🔍 SEARCH OPTIONS:")
        print("  1. Search by SKU (e.g., 'SKU12345')")
        print("  2. Search by product name (e.g., 'headphones')")
        print("  3. View approved price changes")
        print("  4. Help & Examples")
        print("  5. Exit")
        
        choice = input("\n❓ Enter your choice (1-5): ").strip()
        
        if choice == '5':
            print("\n👋 Thank you for using PriceWise!")
            break
        elif choice == '3':
            view_approved_changes()
            input("\n⏸️  Press Enter to continue...")
            continue
        elif choice == '4':
            print_separator("📚 HELP & EXAMPLES", "=")
            print("🔍 Search Examples:")
            print("  • 'SKU12345' - Find specific SKU")
            print("  • 'headphones' - Find all headphone products") 
            print("  • 'electronics' - Find all electronics")
            print("  • 'coffee' - Find coffee-related products")
            print("\n💡 Available SKUs in demo:")
            print("  • SKU12345 - Wireless Headphones")
            print("  • SKU67890 - Running Shoes")
            print("  • SKU54321 - Coffee Maker")
            print("  • SKU11111 - Smart Watch")
            print("  • SKU22222 - Yoga Mat")
            print("  • SKU33333 - Blender")
            input("\n⏸️  Press Enter to continue...")
            continue
        elif choice not in ['1', '2']:
            print("❌ Invalid choice. Please enter 1-5.")
            continue
        
        # Get search query
        search_query = input("\n🔍 Enter SKU or product name: ").strip()
        
        if not search_query:
            print("❌ Please enter a valid search term.")
            continue
        
        # Search for products
        products = search_products(search_query, retriever)
        
        if not products:
            continue
        
        # Select product if multiple found
        if len(products) > 1:
            while True:
                try:
                    selection = input(f"\n❓ Select product (1-{len(products)}): ").strip()
                    selected_idx = int(selection) - 1
                    if 0 <= selected_idx < len(products):
                        selected_product = products[selected_idx]['product']
                        break
                    else:
                        print(f"❌ Please enter a number between 1 and {len(products)}")
                except ValueError:
                    print("❌ Please enter a valid number")
        else:
            selected_product = products[0]['product']
        
        print(f"\n✅ Selected: {selected_product.name} ({selected_product.sku})")
        
        # Show detailed analysis
        display_competitor_analysis(selected_product.sku, retriever)
        display_sales_performance(selected_product.sku, sales_retriever)
        
        # Ask if user wants pricing recommendation
        get_rec = input("\n❓ Get AI pricing recommendation? (y/n): ").strip().lower()
        
        if get_rec not in ['y', 'yes']:
            continue
        
        # Create detailed query for AI
        ai_query = f"""Analyze pricing for {selected_product.name} (SKU: {selected_product.sku}). 
        Current price: ${selected_product.current_price:.2f}, Cost: ${selected_product.cost:.2f}, 
        Stock: {selected_product.stock_level} units. 
        Please provide pricing recommendation considering competitor prices and market conditions."""
        
        # Get AI recommendation
        result = get_pricing_recommendation(selected_product.sku, ai_query, agent)
        
        if not result:
            continue
        
        # Display recommendation
        if not display_recommendation(result):
            continue
        
        # Show detailed reasoning
        show_reasoning = input("\n❓ View detailed AI reasoning? (y/n): ").strip().lower()
        if show_reasoning in ['y', 'yes']:
            print_separator("🧠 AI DETAILED REASONING")
            print(result.get("response", "No detailed reasoning available"))
        
        # Ask for approval
        print_separator("⚖️ APPROVAL DECISION", "=")
        approve = input("❓ Approve this pricing recommendation? (y/n): ").strip().lower()
        
        if approve in ['y', 'yes']:
            # Get new price from recommendation
            if result.get("recommendations"):
                new_price = result["recommendations"][0]['recommended_price']
                
                # Get user notes
                notes = input("📝 Add notes for this change (optional): ").strip()
                
                # Save approved change
                save_approved_change(
                    selected_product.sku, 
                    selected_product.current_price, 
                    new_price, 
                    result,
                    notes
                )
                
                print(f"\n✅ Price change approved!")
                print(f"   📊 {selected_product.sku}: ${selected_product.current_price:.2f} → ${new_price:.2f}")
                print(f"   📁 Saved to approval log for implementation")
                
            else:
                print("❌ No recommendation found to approve")
        else:
            print("❌ Recommendation rejected - no changes saved")
        
        # Continue or exit
        continue_choice = input("\n❓ Search another product? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes']:
            break
    
    print("\n📊 Session Summary:")
    if os.path.exists(APPROVED_CHANGES_FILE):
        try:
            with open(APPROVED_CHANGES_FILE, 'r') as f:
                changes = json.load(f)
            print(f"   ✅ Total approved changes: {len(changes)}")
            print(f"   📁 Details saved in: {APPROVED_CHANGES_FILE}")
            print(f"   📋 Log available in: {PRICE_CHANGE_LOG_CSV}")
        except:
            print("   📄 No changes recorded this session")
    
    print("\n👋 Thank you for using PriceWise Interactive Pricing System!")

if __name__ == "__main__":
    main() 