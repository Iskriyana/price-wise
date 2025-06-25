"""
Enhanced Streamlit UI for Iteration 1: RAG-powered Pricing Agent with Guardrails and Approval Workflow

This provides a streamlined web interface for pricing analysts to interact
with the RAG-powered pricing recommendation system.
"""
import streamlit as st
import pandas as pd
import logging
import sys
import os
from datetime import datetime
from typing import List, Optional

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import (
    PricingQuery, PricingRecommendation, ApprovalRequest, ApprovalStatus, 
    ApprovalLevel, RiskLevel
)
from src.pricing_agent import EnhancedPricingRAGAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="PriceWise AI - Enhanced Pricing Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .recommendation-box {
        background: #ecfdf5;
        border: 1px solid #10b981;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background: #fee2e2;
        border: 1px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .critical-box {
        background: #fef2f2;
        border: 2px solid #dc2626;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .example-box {
        background: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .approval-box {
        background: #fefce8;
        border: 2px solid #eab308;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = "analyst"
if 'user_id' not in st.session_state:
    st.session_state.user_id = "user_" + str(hash(datetime.now()))[:8]
if 'current_recommendation' not in st.session_state:
    st.session_state.current_recommendation = None

def initialize_agent():
    """Initialize the enhanced pricing agent"""
    try:
        with st.spinner("🚀 Initializing Enhanced Pricing Agent..."):
            agent = EnhancedPricingRAGAgent()
            agent.initialize()
            st.session_state.agent = agent
            st.session_state.agent_initialized = True
            st.success("✅ Enhanced Pricing Agent initialized successfully!")
            st.rerun()
            return True
    except Exception as e:
        st.error(f"❌ Failed to initialize agent: {str(e)}")
        return False

def get_approval_authority(role):
    """Get the maximum price change amount this role can approve"""
    approval_limits = {
        "analyst": 50.0,  # Can approve up to $50 change
        "senior_analyst": 150.0,  # Can approve up to $150 change
        "manager": 500.0,  # Can approve up to $500 change
        "director": float('inf')  # Can approve any amount
    }
    return approval_limits.get(role, 50.0)

def can_approve_recommendation(recommendation, user_role):
    """Check if user can approve this recommendation based on price change amount"""
    if not recommendation.product_info or not recommendation.recommended_price:
        return False
    
    current_price = recommendation.product_info[0].current_price
    recommended_price = recommendation.recommended_price
    price_change = abs(recommended_price - current_price)
    
    user_limit = get_approval_authority(user_role)
    
    return price_change <= user_limit

def create_user_profile():
    """Create user profile section"""
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        user_role = st.selectbox(
            "👤 Your Role",
            options=["analyst", "senior_analyst", "manager", "director"],
            index=["analyst", "senior_analyst", "manager", "director"].index(st.session_state.user_role),
            help="Select your role to determine approval authority"
        )
        st.session_state.user_role = user_role
    
    with col2:
        authority_levels = {
            "analyst": "Up to $50 price changes",
            "senior_analyst": "Up to $150 price changes",
            "manager": "Up to $500 price changes", 
            "director": "Any price changes"
        }
        st.info(f"**Approval Authority:** {authority_levels[user_role]}")
    
    with col3:
        st.text(f"**User ID:** {st.session_state.user_id[:8]}")

def create_recommendation_table(recommendations):
    """Create the required output table format"""
    if not recommendations:
        return pd.DataFrame()
    
    if not isinstance(recommendations, list):
        recommendations = [recommendations]
    
    table_data = []
    
    for rec in recommendations:
        if rec.product_info and len(rec.product_info) > 0:
            product = rec.product_info[0]
            product_name = product.item_name
            product_id = product.item_id
        else:
            product_name = "N/A"
            product_id = "N/A"
        
        approval_threshold = rec.approval_threshold.value.replace('_', ' ').title() if rec.approval_threshold else "Analyst"
        recommended_price = f"${rec.recommended_price:.2f}" if rec.recommended_price else "See Analysis"
        short_reasoning = rec.reasoning[:100] + "..." if len(rec.reasoning) > 100 else rec.reasoning
        
        table_data.append({
            "Product": product_name,
            "Product ID": product_id,
            "Approval Threshold": approval_threshold,
            "Recommended Price": recommended_price,
            "Short Reasoning": short_reasoning
        })
    
    return pd.DataFrame(table_data)

def display_approval_section(recommendation):
    """Display approval section with role-based approval button"""
    if recommendation.approval_status != ApprovalStatus.PENDING:
        return
    
    st.markdown('<div class="approval-box">', unsafe_allow_html=True)
    st.subheader("🔄 Approval Required")
    
    user_role = st.session_state.user_role
    can_approve = can_approve_recommendation(recommendation, user_role)
    
    if recommendation.product_info and recommendation.recommended_price:
        current_price = recommendation.product_info[0].current_price
        price_change = abs(recommendation.recommended_price - current_price)
        user_limit = get_approval_authority(user_role)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Price Change Amount", f"${price_change:.2f}")
            st.metric("Your Approval Limit", f"${user_limit:.2f}" if user_limit != float('inf') else "Unlimited")
        
        with col2:
            st.metric("Risk Level", recommendation.risk_level.value.title())
            if recommendation.financial_impact:
                revenue_impact = recommendation.financial_impact.get('estimated_monthly_revenue_impact', 0)
                st.metric("Revenue Impact", f"${revenue_impact:,.0f}/month")
    
    if can_approve:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Approve Recommendation", type="primary", key=f"approve_{recommendation.recommendation_id}"):
                approval_request = ApprovalRequest(
                    recommendation_id=recommendation.recommendation_id,
                    approver_id=st.session_state.user_id,
                    approver_role=user_role,
                    decision=ApprovalStatus.APPROVED,
                    notes=f"Approved by {user_role} - price change within authority limit"
                )
                
                success = st.session_state.agent.submit_approval_request(approval_request)
                if success:
                    st.success("✅ Recommendation approved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to approve recommendation")
        
        with col2:
            if st.button("❌ Reject Recommendation", key=f"reject_{recommendation.recommendation_id}"):
                approval_request = ApprovalRequest(
                    recommendation_id=recommendation.recommendation_id,
                    approver_id=st.session_state.user_id,
                    approver_role=user_role,
                    decision=ApprovalStatus.REJECTED,
                    notes=f"Rejected by {user_role}"
                )
                
                success = st.session_state.agent.submit_approval_request(approval_request)
                if success:
                    st.warning("❌ Recommendation rejected")
                    st.rerun()
                else:
                    st.error("❌ Failed to reject recommendation")
    else:
        if recommendation.product_info and recommendation.recommended_price:
            price_change = abs(recommendation.recommended_price - recommendation.product_info[0].current_price)
            required_role = "director" if price_change > 500 else "manager" if price_change > 150 else "senior_analyst"
            st.warning(f"⚠️ This price change (${price_change:.2f}) requires {required_role} approval or higher. Your role ({user_role}) has insufficient authority.")
        else:
            st.info("⚠️ Cannot determine approval authority - insufficient pricing data.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_recommendation_details(recommendation):
    """Display detailed recommendation information"""
    risk_styles = {
        RiskLevel.LOW: "recommendation-box",
        RiskLevel.MEDIUM: "warning-box", 
        RiskLevel.HIGH: "error-box",
        RiskLevel.CRITICAL: "critical-box"
    }
    
    risk_emoji = {"low": "✅", "medium": "⚠️", "high": "🚨", "critical": "🔥"}
    
    st.markdown(f'<div class="{risk_styles[recommendation.risk_level]}">', unsafe_allow_html=True)
    st.subheader(f"{risk_emoji.get(recommendation.risk_level.value, '💡')} Risk Assessment: {recommendation.risk_level.value.upper()}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        confidence_pct = recommendation.confidence_score * 100
        st.metric("Confidence", f"{confidence_pct:.0f}%")
    
    with col2:
        st.metric("Risk Level", recommendation.risk_level.value.title())
    
    with col3:
        if recommendation.financial_impact:
            revenue_impact = recommendation.financial_impact.get('estimated_monthly_revenue_impact', 0)
            st.metric("Revenue Impact", f"${revenue_impact:,.0f}/month")
        else:
            st.metric("Revenue Impact", "N/A")
    
    with col4:
        products_analyzed = len(recommendation.product_info)
        st.metric("Products Analyzed", products_analyzed)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Guardrail violations if any
    if recommendation.guardrail_violations:
        st.subheader("🛡️ Guardrail Adjustments")
        for violation in recommendation.guardrail_violations:
            st.warning(f"**{violation.rule_name.replace('_', ' ').title()}**: {violation.explanation}")
    
    # Approval section
    display_approval_section(recommendation)
    
    # Full reasoning in expandable section
    with st.expander("📋 View Full Analysis"):
        st.subheader("Detailed Reasoning")
        st.text_area("Analysis", recommendation.reasoning, height=200, disabled=True, key=f"full_reasoning_{recommendation.recommendation_id}")
        
        if recommendation.market_context:
            st.subheader("Market Context")
            st.text_area("Market Analysis", recommendation.market_context, height=150, disabled=True, key=f"market_context_{recommendation.recommendation_id}")

def create_example_queries():
    """Create example queries at the top for users to try"""
    st.markdown('<div class="example-box">', unsafe_allow_html=True)
    st.subheader("💡 Try These Example Queries")
    
    examples = [
        {
            "title": "⚡ Flash Sale Optimization",
            "query": "What should be the optimal price for Nike Air Max sneakers (APP10001) during a 6-hour flash sale event?",
            "context": "Flash sale event - high demand expected, need to balance inventory and revenue",
            "product_ids": "APP10001"
        },
        {
            "title": "🛍️ Black Friday Strategy",
            "query": "Optimize pricing for Adidas T-shirts during Black Friday considering competitor price drops and high inventory levels",
            "context": "Black Friday event - competitors reduced prices by 15%, high inventory needs clearance",
            "product_ids": ""
        },
        {
            "title": "🚨 Stockout Prevention",
            "query": "Product APP10000 is selling 3x faster than expected. Should we increase the price to prevent stockout?",
            "context": "High-velocity sales event - demand surge detected, limited inventory",
            "product_ids": "APP10000"
        },
        {
            "title": "📊 Demand Simulation",
            "query": "Simulate demand scenarios for Under Armour Socks (APP10005) with ±10% price changes during peak sales period",
            "context": "Peak sales period - need price elasticity analysis and revenue optimization",
            "product_ids": "APP10005"
        }
    ]
    
    col1, col2 = st.columns(2)
    
    for i, example in enumerate(examples):
        with col1 if i % 2 == 0 else col2:
            if st.button(f"{example['title']}", key=f"example_{i}", use_container_width=True):
                st.session_state.example_query = example['query']
                st.session_state.example_context = example['context']
                st.session_state.example_product_ids = example['product_ids']
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>⚡ PriceWise AI - Real-Time Pricing Agent</h1>
        <p>High-Velocity Sales Event Optimizer with Price Elasticity Modeling & Demand Simulation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize agent if needed
    if not st.session_state.agent_initialized:
        st.info("⚡ Welcome to Real-Time PriceWise AI! Click below to initialize the high-velocity pricing agent.")
        if st.button("Initialize Real-Time Pricing Agent", type="primary"):
            initialize_agent()
        return
    
    # User profile
    create_user_profile()
    st.markdown("---")
    
    # Example queries at the top
    create_example_queries()
    st.markdown("---")
    
    # Main query interface
    st.subheader("⚡ Ask the Real-Time Pricing Agent")
    
    # Query form
    with st.form("pricing_query"):
        # Check for example query in session state
        default_query = st.session_state.get('example_query', '')
        default_context = st.session_state.get('example_context', '')
        default_product_ids = st.session_state.get('example_product_ids', '')
        
        # Clear example from session state after using
        if 'example_query' in st.session_state:
            del st.session_state.example_query
            del st.session_state.example_context  
            del st.session_state.example_product_ids
        
        query = st.text_area(
            "Your Real-Time Pricing Question",
            value=default_query,
            placeholder="e.g., What should be the optimal price for Nike sneakers during a flash sale to maximize revenue while managing inventory?",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            context = st.text_input(
                "Additional Context (Optional)",
                value=default_context,
                placeholder="e.g., Competitor analysis, margin optimization"
            )
        
        with col2:
            product_ids = st.text_input(
                "Specific Product IDs (Optional)",
                value=default_product_ids,
                placeholder="e.g., APP10000, APP10001"
            )
        
        submitted = st.form_submit_button("🔍 Get Pricing Recommendation", type="primary")
    
    if submitted and query.strip():
        try:
            # Parse product IDs
            product_id_list = [pid.strip() for pid in product_ids.split(',') if pid.strip()] if product_ids else None
            
            # Create query object
            pricing_query = PricingQuery(
                query=query,
                context=context if context else None,
                product_ids=product_id_list,
                requester_id=st.session_state.user_id,
                requester_role=st.session_state.user_role
            )
            
            # Process query
            with st.spinner("🤖 Analyzing your pricing question with guardrails..."):
                recommendation = st.session_state.agent.process_query(pricing_query)
            
            # Store current recommendation
            st.session_state.current_recommendation = recommendation
            
            # Display results in required table format
            st.success("✅ Analysis Complete!")
            
            # Create and display the required table
            st.subheader("📊 Pricing Recommendation Results")
            recommendation_table = create_recommendation_table([recommendation])
            
            if not recommendation_table.empty:
                st.dataframe(
                    recommendation_table,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Display detailed analysis below the table
                st.markdown("---")
                display_recommendation_details(recommendation)
            else:
                st.warning("No specific pricing recommendations generated. Please try a more specific query.")
                st.text_area("Raw Response", recommendation.reasoning, height=200, disabled=True)
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")
            logger.error(f"Query processing error: {str(e)}")
    
    elif submitted:
        st.warning("⚠️ Please enter a pricing question.")

if __name__ == "__main__":
    main() 