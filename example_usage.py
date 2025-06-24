#!/usr/bin/env python3
"""
Example usage of the PriceWise Pricing Agent (Iteration 2)

This script demonstrates how to use the semi-autonomous pricing agent
with RAG, recommendations, and financial simulation capabilities.
"""

import os
import asyncio
from dotenv import load_dotenv
from src.pricing_agent import create_pricing_agent

# Load environment variables
load_dotenv()

def print_separator(title=""):
    """Print a nice separator for better readability"""
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)

def print_analysis_result(result):
    """Pretty print the analysis result"""
    print("\n📊 ANALYSIS COMPLETE!")
    print("-" * 50)
    
    print("\n📋 RECOMMENDATIONS:")
    for i, rec in enumerate(result["recommendations"], 1):
        print(f"\n  {i}. SKU: {rec['sku']}")
        print(f"     Current Price: ${rec['current_price']:.2f}")
        print(f"     Recommended Price: ${rec['recommended_price']:.2f}")
        print(f"     Price Change: {rec['price_change_percent']:+.1f}%")
        print(f"     Confidence: {rec['confidence_score']:.1%}")
    
    print("\n💰 FINANCIAL SIMULATIONS:")
    for i, sim in enumerate(result["simulations"], 1):
        print(f"\n  {i}. SKU: {sim['sku']}")
        print(f"     Revenue Change: ${sim['projected_revenue_change']:+,.2f}")
        print(f"     Profit Change: ${sim['projected_profit_change']:+,.2f}")
        print(f"     Demand Change: {sim['estimated_demand_change']:+.1f}%")
        print(f"     Risk Level: {sim['risk_level']}")
    
    print(f"\n✅ Human Approval Required: {result['approval_required']}")
    
    print("\n📝 CONVERSATION HISTORY:")
    for i, msg in enumerate(result["conversation_history"], 1):
        print(f"  {i}. {msg}")

def main():
    """Main function demonstrating the pricing agent"""
    
    print_separator("PriceWise Pricing Agent - Iteration 2 Demo")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Please copy env.example to .env and add your OpenAI API key")
        return
    
    try:
        print("🚀 Initializing pricing agent...")
        agent = create_pricing_agent()
        print("✅ Agent initialized successfully!")
        
        # Example queries to test
        example_queries = [
            {
                "title": "Competitor Price Response",
                "query": "What is the recommended price for wireless headphones SKU12345 given that Amazon lowered their price to $89.99?",
                "description": "Testing competitor price analysis and recommendation generation"
            },
            {
                "title": "Multi-Product Analysis", 
                "query": "Analyze pricing for running shoes and coffee maker based on current stock levels and sales performance",
                "description": "Testing multi-product analysis with inventory considerations"
            },
            {
                "title": "Sales-Driven Analysis",
                "query": "Should we adjust prices for SKU67890 running shoes based on recent sales performance?",
                "description": "Testing sales-driven pricing recommendations"
            }
        ]
        
        # Run examples
        for i, example in enumerate(example_queries, 1):
            print_separator(f"Example {i}: {example['title']}")
            print(f"📋 Description: {example['description']}")
            print(f"❓ Query: {example['query']}")
            
            try:
                print("\n⏳ Running analysis...")
                result = agent.run_analysis(example["query"])
                print_analysis_result(result)
                
                print("\n📄 FULL RESPONSE:")
                print(result["response"])
                
            except Exception as e:
                print(f"❌ Error running analysis: {e}")
            
            # Ask user if they want to continue
            if i < len(example_queries):
                input("\n⏸️  Press Enter to continue to next example...")
        
        # Interactive mode
        print_separator("Interactive Mode")
        print("💬 Now you can ask your own pricing questions!")
        print("   Type 'quit' to exit")
        
        while True:
            query = input("\n🤔 Your pricing question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                print("   Please enter a valid query")
                continue
            
            try:
                print("⏳ Analyzing...")
                result = agent.run_analysis(query)
                print_analysis_result(result)
                
                # Ask if user wants to see full response
                show_full = input("\n❓ Show full response? (y/n): ").strip().lower()
                if show_full in ['y', 'yes']:
                    print("\n📄 FULL RESPONSE:")
                    print(result["response"])
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n👋 Thanks for using PriceWise!")
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return

if __name__ == "__main__":
    main() 