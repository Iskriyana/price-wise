"""
Streamlit UI for Iteration 2: Multi-Query AI Pricing Assistant & Recommendation Dashboard

This provides a more advanced, two-part web interface for pricing analysts:
1.  A query interface for iterative analysis of products.
2.  A final recommendation dashboard to summarize the session's findings.
"""
import streamlit as st
import pandas as pd
import logging
import sys
import os
from datetime import datetime
from typing import List
import re

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import (
    PricingQuery, PricingRecommendation, ApprovalStatus, ApprovalLevel
)
from src.pricing_agent import EnhancedPricingRAGAgent

# --- Page Configuration & Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="PriceWise AI - Pricing Assistant",
    page_icon="💡",
    layout="wide"
)

# --- Session State Initialization ---
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False
if 'recommendation_history' not in st.session_state:
    st.session_state.recommendation_history = []
if 'view' not in st.session_state:
    st.session_state.view = 'query' # Two views: 'query' and 'dashboard'
if 'user_id' not in st.session_state:
    st.session_state.user_id = "analyst_" + str(hash(datetime.now()))[1:9]
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'dashboard_approved' not in st.session_state:
    st.session_state.dashboard_approved = False

# --- Agent Initialization ---
def initialize_agent():
    """Initialize the pricing agent and store it in session state."""
    try:
        with st.spinner("🚀 Initializing PriceWise AI Agent... This may take a moment."):
            agent = EnhancedPricingRAGAgent()
            agent.initialize()
            st.session_state.agent = agent
            st.session_state.agent_initialized = True
        st.success("✅ PriceWise AI Agent is ready!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Critical Error: Failed to initialize agent. Please check logs. Error: {e}")

# --- UI Rendering Functions ---

def render_query_interface():
    """Renders the main interface for users to ask pricing questions."""
    st.header("Step 1: Analyze Products")
    st.write("Ask questions about one or more products to generate pricing recommendations. Each successful recommendation will be added to the dashboard.")

    # Query Input Form
    with st.form("query_form"):
        query = st.text_area(
            "Enter your pricing query",
            value=st.session_state.last_query,
            placeholder="e.g., 'What is the optimal price for Nike sneakers?' or 'Compare pricing for APP10001 and APP10002'",
            height=100
        )
        submitted = st.form_submit_button("🧠 Get Recommendation")

    # Processing Logic
    if submitted and query:
        st.session_state.last_query = query
        process_query(query)
    elif submitted:
        st.warning("Please enter a query.")

    st.markdown("---")

    # Display current recommendations and finalize button
    if st.session_state.recommendation_history:
        st.subheader("Analyzed Products in this Session")
        
        for rec in st.session_state.recommendation_history:
            if rec.product_info and rec.recommended_price is not None:
                product = rec.product_info[0]
                with st.expander(f"**{product.item_name}** | Recommended Price: **${rec.recommended_price:.2f}**"):
                    
                    st.subheader("Pricing Recommendation Results")
                    
                    price_change_abs = rec.recommended_price - product.current_price
                    
                    # Use the calculated percentage from financial_impact for consistency
                    if rec.financial_impact and 'price_change_percent' in rec.financial_impact:
                        price_change_pct = rec.financial_impact['price_change_percent']
                    else:
                        # Fallback calculation
                        price_change_pct = (price_change_abs / product.current_price * 100) if product.current_price > 0 else 0
                    
                    if price_change_abs > 0.01:
                        action = "Increase"
                    elif price_change_abs < -0.01:
                        action = "Decrease"
                    else:
                        action = "No Change"

                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    col1.metric("Recommended Action", action)
                    col2.metric("Current Price", f"${product.current_price:,.2f}")
                    col3.metric("Price Change", f"${price_change_abs:,.2f}", f"{price_change_pct:.1f}%", delta_color="off")
                    
                    revenue_impact = 0
                    if rec.financial_impact:
                        revenue_impact = rec.financial_impact.get('estimated_monthly_revenue_impact', 0)
                    col4.metric("Revenue Impact (p.m.)", f"${revenue_impact:,.0f}")
                    
                    col5.metric("Confidence Level", f"{rec.confidence_score:.0%}")
                    col6.metric("Risk Level", rec.risk_level.value.title())

                    # --- Analysis Section ---
                    st.subheader("Analysis")
                    st.text_area(f"Detailed Reasoning ({product.item_id})", value=rec.reasoning, height=150, disabled=True, key=f"query_reasoning_{product.item_id}")
                    if rec.market_context:
                        st.text_area(f"Market Context ({product.item_id})", value=rec.market_context, height=150, disabled=True, key=f"query_market_{product.item_id}")

        if st.button("Step 2: Finalize and View Dashboard ➡️", type="primary"):
            st.session_state.view = 'dashboard'
            st.rerun()

def _get_processed_product_ids() -> List[str]:
    """Returns a list of all product IDs in the current recommendation history."""
    processed_ids = []
    for rec in st.session_state.recommendation_history:
        if rec.product_info:
            for product in rec.product_info:
                processed_ids.append(product.item_id)
    return processed_ids

def process_query(query: str):
    """Handles the query submission, agent processing, and response display."""
    with st.spinner("🔍 Analyzing..."):
        pricing_query = PricingQuery(
            query=query,
            requester_id=st.session_state.user_id
        )
        recommendation = st.session_state.agent.process_query(pricing_query)

        # Post-processing duplicate check
        if recommendation.product_info:
            product_id = recommendation.product_info[0].item_id
            product_name = recommendation.product_info[0].item_name
            processed_ids = _get_processed_product_ids()
            if product_id in processed_ids:
                st.warning(f"Item **{product_name} ({product_id})** has already been analyzed in this session. The result was not added again.", icon="⚠️")
                return # Stop processing to prevent duplicates

        # Check for guardrail rejection
        if recommendation.approval_status == ApprovalStatus.REJECTED and recommendation.reasoning:
            st.error(f"⚠️ **Request Blocked**: {recommendation.reasoning}", icon="🛡️")
        # Check for other errors
        elif not recommendation.product_info and not recommendation.recommended_price:
            st.warning(f"**Could not generate a specific recommendation.**\n\nAgent's analysis: *{recommendation.reasoning}*", icon="🤔")
        # Handle success
        else:
            st.session_state.recommendation_history.append(recommendation)
            st.success(f"✅ Recommendation for **{recommendation.product_info[0].item_name}** added to the dashboard.", icon="🎉")
            # Clear query box for next query
            st.session_state.last_query = ""
            st.rerun()

def render_dashboard():
    """Renders the final summary dashboard of all recommendations."""
    st.header("Step 2: Recommendation Dashboard")
    st.write("This dashboard summarizes all pricing recommendations from your analysis session.")

    if not st.session_state.recommendation_history:
        st.warning("No recommendations have been generated yet. Please go back and analyze some products.")
        if st.button("⬅️ Back to Analysis"):
            st.session_state.view = 'query'
            st.rerun()
        return

    # Prepare data for the summary dataframe
    dashboard_data = []
    for rec in st.session_state.recommendation_history:
        if not rec.product_info: continue
        
        product = rec.product_info[0]
        price_change = rec.recommended_price - product.current_price if rec.recommended_price else 0
        
        # Format price change with color
        if price_change > 0.01:
            price_change_display = f"+${price_change:.2f}"
        elif price_change < -0.01:
            price_change_display = f"-${abs(price_change):.2f}"
        else:
            price_change_display = "$0.00"
        
        dashboard_data.append({
            "Product Name": product.item_name,
            "Product ID": product.item_id,
            "Current Price": f"${product.current_price:.2f}",
            "Recommended Price": f"${rec.recommended_price:.2f}" if rec.recommended_price else "N/A",
            "Price Change": price_change_display,
            "Risk Level": rec.risk_level.value.title(),
            "Required Approval": rec.approval_threshold.value.replace('_', ' ').title(),
            "Analysis": rec.reasoning
        })
    
    for rec in st.session_state.recommendation_history:
        if not rec.product_info or rec.recommended_price is None: continue
        
        product = rec.product_info[0]
        with st.container(border=True):
            price_change_abs = rec.recommended_price - product.current_price
            if price_change_abs > 0.01:
                action = "Increase"
            elif price_change_abs < -0.01:
                action = "Decrease"
            else:
                action = "No Change"

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.text("Product Name"); col1.write(f"**{product.item_name}**")
            col2.text("Brand"); col2.write(f"**{product.item_name.split()[0]}**")
            col3.text("Current Price"); col3.write(f"**${product.current_price:.2f}**")
            
            # Color-coded action and price change
            if price_change_abs > 0.01:
                col4.text("Recommended Action"); col4.write(f"**:green[{action}]**")
                col5.text("Recommended Price"); col5.write(f"**:green[${rec.recommended_price:.2f}]** (:green[+${price_change_abs:.2f}])")
            elif price_change_abs < -0.01:
                col4.text("Recommended Action"); col4.write(f"**:red[{action}]**")
                col5.text("Recommended Price"); col5.write(f"**:red[${rec.recommended_price:.2f}]** (:red[-${abs(price_change_abs):.2f}])")
            else:
                col4.text("Recommended Action"); col4.write(f"**{action}**")
                col5.text("Recommended Price"); col5.write(f"**${rec.recommended_price:.2f}** (No Change)")

            revenue_impact = 0
            if rec.financial_impact:
                revenue_impact = rec.financial_impact.get('estimated_monthly_revenue_impact', 0)
            col6.text("Revenue Impact (p.m.)"); col6.write(f"**${revenue_impact:,.0f}**")

            # Expander for full details
            with st.expander("Show Full Reasoning and Analysis"):
                st.text_area(f"Reasoning ({product.item_id})", value=rec.reasoning, height=150, disabled=True, key=f"reasoning_{product.item_id}")
                st.text_area(f"Market Context ({product.item_id})", value=rec.market_context, height=150, disabled=True, key=f"market_{product.item_id}")

                if rec.guardrail_violations:
                    st.warning("Guardrail Adjustments Applied:", icon="🛡️")
                    for violation in rec.guardrail_violations:
                        st.write(f"- **{violation.rule_name.replace('_', ' ').title()}**: {violation.explanation}")
    
    st.markdown("---")

    # --- Final Approval Step ---
    if not st.session_state.dashboard_approved:
        st.subheader("Step 3: Final Approval")
        st.info("Please review the detailed analysis above before finalizing the summary.", icon="ℹ️")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve & Finalize Summary", type="primary"):
                st.session_state.dashboard_approved = True
                st.rerun()
        with col2:
            if st.button("❌ Reject All"):
                st.error("No approval provided. The summary will not be generated. You can start a new session or go back to the analysis step.", icon="🚫")

    # --- Summary and Download (only shows after approval) ---
    if st.session_state.dashboard_approved:
        st.subheader("Summary of Recommendations")
        summary_df = pd.DataFrame(dashboard_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        csv = summary_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Summary as CSV",
            data=csv,
            file_name='pricing_recommendation_summary.csv',
            mime='text/csv',
        )

    st.markdown("---")
    if st.button("⬅️ Start New Analysis Session"):
        # Clear history for a new session
        st.session_state.recommendation_history = []
        st.session_state.dashboard_approved = False
        st.session_state.view = 'query'
        st.rerun()


# --- Main Application Logic ---
def main():
    """Main function to run the Streamlit app."""
    st.title("💡 PriceWise AI Assistant")

    if not st.session_state.agent_initialized:
        st.warning("The AI agent is not yet initialized.")
        if st.button("Click to Initialize Agent", type="primary"):
            initialize_agent()
    else:
        # User can switch between views
        if st.session_state.view == 'query':
            render_query_interface()
        elif st.session_state.view == 'dashboard':
            render_dashboard()

if __name__ == "__main__":
    main()