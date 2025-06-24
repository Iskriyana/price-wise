#!/usr/bin/env python3
"""
PriceWise Streamlit Demo App

A beautiful web interface for the intelligent pricing system featuring:
- SKU search and product analysis
- AI-powered pricing recommendations  
- Financial impact simulation
- Approval workflow with tracking
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import PriceWise components
try:
    from src.pricing_agent import create_pricing_agent
    from src.tools import ProductDataRetriever, SalesDataRetriever
    from src.models import ProductInfo, CompetitorPrice
except ImportError as e:
    st.error(f"Error importing PriceWise components: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="PriceWise - Intelligent Pricing System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
    }
    .recommendation-box {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #2196f3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'pricing_agent' not in st.session_state:
    st.session_state.pricing_agent = None
if 'product_retriever' not in st.session_state:
    st.session_state.product_retriever = None
if 'sales_retriever' not in st.session_state:
    st.session_state.sales_retriever = None
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None
if 'recommendation_result' not in st.session_state:
    st.session_state.recommendation_result = None
if 'approved_changes' not in st.session_state:
    st.session_state.approved_changes = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🔍 Product Search"

def initialize_system():
    """Initialize the PriceWise system components"""
    try:
        with st.spinner("🚀 Initializing PriceWise system..."):
            st.session_state.pricing_agent = create_pricing_agent()
            st.session_state.product_retriever = ProductDataRetriever()
            st.session_state.sales_retriever = SalesDataRetriever()
        return True
    except Exception as e:
        st.error(f"Failed to initialize system: {e}")
        return False

def load_approved_changes():
    """Load approved changes from file"""
    if os.path.exists("approved_price_changes.json"):
        try:
            with open("approved_price_changes.json", 'r') as f:
                st.session_state.approved_changes = json.load(f)
        except:
            st.session_state.approved_changes = []

def save_approved_change(sku: str, old_price: float, new_price: float, 
                        recommendation_data: Dict, user_notes: str = ""):
    """Save approved price change"""
    timestamp = datetime.now().isoformat()
    
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
    
    # Load existing changes
    if os.path.exists("approved_price_changes.json"):
        try:
            with open("approved_price_changes.json", 'r') as f:
                approved_changes = json.load(f)
        except:
            approved_changes = []
    else:
        approved_changes = []
    
    # Add new change
    approved_changes.append(change_record)
    
    # Save to file
    with open("approved_price_changes.json", 'w') as f:
        json.dump(approved_changes, f, indent=2)
    
    # Update session state
    st.session_state.approved_changes = approved_changes
    
    return True

def render_product_card(product: ProductInfo):
    """Render a product information card"""
    margin = ((product.current_price - product.cost) / product.current_price) * 100
    margin_color = "🟢" if margin > 40 else "🟡" if margin > 20 else "🔴"
    
    with st.container():
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏷️ {product.name}</h3>
            <p><strong>SKU:</strong> {product.sku}</p>
            <p><strong>Category:</strong> {product.category}</p>
            <p><strong>Current Price:</strong> ${product.current_price:.2f}</p>
            <p><strong>Cost:</strong> ${product.cost:.2f}</p>
            <p><strong>Stock:</strong> {product.stock_level} units</p>
            <p><strong>Margin:</strong> {margin_color} {margin:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

def render_competitor_analysis(sku: str):
    """Render competitor pricing analysis"""
    if st.session_state.product_retriever:
        competitors = st.session_state.product_retriever.retrieve_competitor_data(sku)
        
        if competitors:
            st.markdown("### 🔍 Competitor Analysis")
            
            # Create competitor data for chart
            comp_data = []
            for comp in competitors:
                hours_ago = int((datetime.now() - comp.last_updated).total_seconds() / 3600)
                comp_data.append({
                    'Competitor': comp.competitor_name,
                    'Price': comp.price,
                    'Confidence': f"{comp.product_match_confidence:.1%}",
                    'Last Updated': f"{hours_ago}h ago"
                })
            
            # Display as table
            df_comp = pd.DataFrame(comp_data)
            st.dataframe(df_comp, use_container_width=True)
            
            # Create price comparison chart
            fig = px.bar(df_comp, x='Competitor', y='Price', 
                        title="Competitor Price Comparison",
                        color='Price', color_continuous_scale='Blues')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⚠️ No competitor data available for this SKU")

def render_sales_performance(sku: str):
    """Render sales performance analysis"""
    if st.session_state.sales_retriever:
        sales_data = st.session_state.sales_retriever.get_sales_data(sku, days=30)
        
        st.markdown("### 📈 Sales Performance (30 Days)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Units Sold", f"{sales_data.units_sold:,}")
        
        with col2:
            st.metric("Revenue", f"${sales_data.revenue:,.2f}")
        
        with col3:
            st.metric("Daily Velocity", f"{sales_data.velocity:.1f} units/day")
        
        # Performance classification
        if sales_data.velocity > 20:
            performance = "🚀 High Performer"
        elif sales_data.velocity > 10:
            performance = "📈 Good Performer"
        elif sales_data.velocity > 5:
            performance = "📊 Average Performer"
        else:
            performance = "🔻 Slow Mover"
        
        st.markdown(f"**Performance Classification:** {performance}")

def render_recommendation_result(result: Dict[str, Any]):
    """Render AI recommendation with styling"""
    if not result or not result.get("recommendations"):
        return None
    
    rec = result["recommendations"][0]
    
    st.markdown("""
    <div class="recommendation-box">
        <h3>🎯 AI Pricing Recommendation</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Price", f"${rec['current_price']:.2f}")
    
    with col2:
        change = rec['recommended_price'] - rec['current_price']
        change_percent = (change / rec['current_price']) * 100
        st.metric("Recommended Price", f"${rec['recommended_price']:.2f}", 
                 f"{change:+.2f} ({change_percent:+.1f}%)")
    
    with col3:
        confidence = rec['confidence_score']
        conf_color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
        st.metric("Confidence", f"{conf_color} {confidence:.1%}")
    
    # Financial simulation
    if result.get("simulations"):
        sim = result["simulations"][0]
        
        st.markdown("### 💰 Financial Impact Simulation")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            rev_change = sim['projected_revenue_change']
            st.metric("Revenue Impact", f"${rev_change:+,.2f}")
        
        with col2:
            profit_change = sim['projected_profit_change']
            st.metric("Profit Impact", f"${profit_change:+,.2f}")
        
        with col3:
            demand_change = sim['estimated_demand_change']
            st.metric("Demand Change", f"{demand_change:+.1f}%")
        
        with col4:
            risk = sim['risk_level']
            risk_colors = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
            st.metric("Risk Level", f"{risk_colors.get(risk, '⚪')} {risk}")
        
        # Create impact visualization
        impact_data = {
            'Metric': ['Revenue', 'Profit'],
            'Change': [rev_change, profit_change]
        }
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=impact_data['Metric'],
            y=impact_data['Change'],
            name='Financial Impact ($)',
            marker_color=['green' if x > 0 else 'red' for x in impact_data['Change']]
        ))
        
        fig.update_layout(
            title="Financial Impact Overview",
            yaxis_title="Change ($)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    return rec

def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<h1 class="main-header">🎯 PriceWise</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Intelligent Pricing System with AI-Powered Recommendations</p>', unsafe_allow_html=True)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("🔑 OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        st.stop()
    
    # Initialize system
    if st.session_state.pricing_agent is None:
        if not initialize_system():
            st.stop()
        st.success("✅ PriceWise system initialized successfully!")
    
    # Load existing approved changes
    load_approved_changes()
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🔍 Product Search", "📊 Pricing Analysis", "📋 Approved Changes", "ℹ️ About"],
        index=["🔍 Product Search", "📊 Pricing Analysis", "📋 Approved Changes", "ℹ️ About"].index(st.session_state.current_page)
    )
    
    # Update current page in session state
    st.session_state.current_page = page
    
    if page == "🔍 Product Search":
        render_search_page()
    elif page == "📊 Pricing Analysis":
        render_analysis_page()
    elif page == "📋 Approved Changes":
        render_approved_changes_page()
    elif page == "ℹ️ About":
        render_about_page()

def render_search_page():
    """Render the product search page"""
    st.header("🔍 Product Search & Analysis")
    
    # Search input
    search_method = st.radio(
        "Search method:",
        ["🏷️ Search by SKU", "📦 Search by Product Name", "🏪 Search by Category"]
    )
    
    if search_method == "🏷️ Search by SKU":
        search_query = st.text_input(
            "Enter SKU:",
            placeholder="e.g., SKU12345",
            help="Enter the exact SKU code"
        )
    elif search_method == "📦 Search by Product Name":
        search_query = st.text_input(
            "Enter product name:",
            placeholder="e.g., headphones, coffee maker",
            help="Enter product name or keywords"
        )
    else:  # Category search
        search_query = st.selectbox(
            "Select category:",
            ["electronics", "sports", "appliances", ""]
        )
    
    # Search button
    if st.button("🔍 Search Products", type="primary"):
        if search_query:
            with st.spinner("Searching products..."):
                products = st.session_state.product_retriever.retrieve_product_info(search_query)
            
            if products:
                st.success(f"Found {len(products)} product(s)")
                
                # Display products
                for i, product in enumerate(products):
                    with st.expander(f"📦 {product.name} ({product.sku})", expanded=(i==0)):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            render_product_card(product)
                        
                        with col2:
                            if st.button(f"🎯 Analyze {product.sku}", key=f"analyze_{product.sku}", type="primary"):
                                with st.spinner("Preparing analysis..."):
                                    st.session_state.selected_product = product
                                    st.session_state.current_page = "📊 Pricing Analysis"
                                st.success("✅ Product selected for analysis!")
                                st.rerun()
                        
                        # Show competitor analysis and sales for expanded product
                        if i == 0:
                            render_competitor_analysis(product.sku)
                            render_sales_performance(product.sku)
            else:
                st.warning("No products found. Try different search terms.")
        else:
            st.warning("Please enter a search term.")

def render_analysis_page():
    """Render the pricing analysis page"""
    st.header("📊 Pricing Analysis & Recommendations")
    
    if st.session_state.selected_product is None:
        st.info("Please select a product from the Search page first.")
        return
    
    product = st.session_state.selected_product
    
    # Display selected product
    st.markdown("### Selected Product")
    render_product_card(product)
    
    # Analysis options
    st.markdown("### Analysis Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        scenario = st.selectbox(
            "Business Scenario:",
            [
                "Competitive Response",
                "Inventory Clearance", 
                "New Product Launch",
                "Cost Increase Impact",
                "General Optimization"
            ]
        )
    
    with col2:
        context = st.text_area(
            "Additional Context:",
            placeholder="e.g., Amazon dropped price to $89.99 for Black Friday",
            height=100
        )
    
    # Generate recommendation
    if st.button("🤖 Get AI Recommendation", type="primary"):
        # Create AI query
        ai_query = f"""
        Analyze pricing for {product.name} (SKU: {product.sku}).
        Current price: ${product.current_price:.2f}, Cost: ${product.cost:.2f}, Stock: {product.stock_level} units.
        Business scenario: {scenario}
        Context: {context if context else 'Standard pricing analysis'}
        Please provide optimal pricing recommendation.
        """
        
        with st.spinner("🧠 AI analyzing market conditions..."):
            try:
                result = st.session_state.pricing_agent.run_analysis(ai_query)
                st.session_state.recommendation_result = result
                
                if result:
                    st.success("✅ Analysis complete!")
                    
                    # Render recommendation
                    rec = render_recommendation_result(result)
                    
                    if rec:
                        # Detailed reasoning
                        with st.expander("🧠 View Detailed AI Reasoning"):
                            st.markdown(result.get("response", "No detailed reasoning available"))
                        
                        # Approval section
                        st.markdown("### ⚖️ Approval Decision")
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            user_notes = st.text_area(
                                "Notes for this change:",
                                placeholder="e.g., Black Friday competitive response",
                                help="Add context or reasoning for the approval"
                            )
                        
                        with col2:
                            st.markdown("<br>", unsafe_allow_html=True)  # Spacer
                            
                            if st.button("✅ Approve Change", type="primary"):
                                # Save approved change
                                success = save_approved_change(
                                    product.sku,
                                    product.current_price,
                                    rec['recommended_price'],
                                    result,
                                    user_notes
                                )
                                
                                if success:
                                    st.success(f"""
                                    ✅ **Price Change Approved!**
                                    
                                    📊 {product.sku}: ${product.current_price:.2f} → ${rec['recommended_price']:.2f}
                                    
                                    📁 Saved to approval log for implementation
                                    """)
                                    
                                    # Show balloons for success
                                    st.balloons()
                                else:
                                    st.error("Failed to save approved change")
                            
                            if st.button("❌ Reject", type="secondary"):
                                st.warning("Recommendation rejected - no changes saved")
                                st.session_state.recommendation_result = None
                                st.rerun()
                
                else:
                    st.error("Failed to get recommendation from AI")
                    
            except Exception as e:
                st.error(f"Error during analysis: {e}")

def render_approved_changes_page():
    """Render the approved changes tracking page"""
    st.header("📋 Approved Price Changes")
    
    if not st.session_state.approved_changes:
        st.info("No approved price changes yet. Go to Pricing Analysis to approve some changes!")
        return
    
    # Summary metrics
    total_changes = len(st.session_state.approved_changes)
    total_price_impact = sum(change['price_change'] for change in st.session_state.approved_changes)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Approved Changes", total_changes)
    
    with col2:
        st.metric("Net Price Impact", f"${total_price_impact:+.2f}")
    
    with col3:
        avg_change = total_price_impact / total_changes if total_changes > 0 else 0
        st.metric("Average Change", f"${avg_change:+.2f}")
    
    # Recent changes
    st.markdown("### Recent Approved Changes")
    
    for i, change in enumerate(reversed(st.session_state.approved_changes[-10:]), 1):
        timestamp = datetime.fromisoformat(change['timestamp'])
        
        with st.expander(f"{i}. {change['sku']} - {timestamp.strftime('%Y-%m-%d %H:%M')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                **SKU:** {change['sku']}
                
                **Price Change:** ${change['old_price']:.2f} → ${change['new_price']:.2f}
                
                **Change:** ${change['price_change']:+.2f} ({change['price_change_percent']:+.1f}%)
                
                **Notes:** {change.get('user_notes', 'No notes provided')}
                
                **Status:** {change['status']}
                """)
            
            with col2:
                # Create a simple gauge chart for the price change
                change_percent = abs(change['price_change_percent'])
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = change_percent,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Change %"},
                    gauge = {
                        'axis': {'range': [None, 20]},
                        'bar': {'color': "green" if change['price_change'] < 0 else "red"},
                        'steps': [
                            {'range': [0, 5], 'color': "lightgray"},
                            {'range': [5, 10], 'color': "gray"},
                            {'range': [10, 20], 'color': "darkgray"}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': 15
                        }
                    }
                ))
                fig.update_layout(height=200)
                st.plotly_chart(fig, use_container_width=True)
    
    # Download options
    st.markdown("### 📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Download as CSV"):
            # Convert to DataFrame
            df = pd.DataFrame(st.session_state.approved_changes)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"approved_changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📋 Download as JSON"):
            json_data = json.dumps(st.session_state.approved_changes, indent=2)
            
            st.download_button(
                label="💾 Download JSON",
                data=json_data,
                file_name=f"approved_changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def render_about_page():
    """Render the about page"""
    st.header("ℹ️ About PriceWise")
    
    st.markdown("""
    ## 🎯 Intelligent Pricing System (Iteration 2)
    
    PriceWise is a comprehensive **semi-autonomous pricing agent** that combines:
    
    ### ✨ Key Features
    - **🔍 Smart SKU Search** - Find products by SKU, name, or category
    - **🤖 AI-Powered Recommendations** - LangGraph-based pricing agent with ReAct reasoning
    - **💰 Financial Impact Simulation** - Revenue, profit, and demand projections
    - **⚖️ Human-in-the-Loop Approval** - Complete audit trail with user notes
    - **📊 Comprehensive Tracking** - JSON and CSV export capabilities
    
    ### 🏪 Available Test Products
    - **SKU12345** - Wireless Bluetooth Headphones ($99.99)
    - **SKU67890** - Athletic Running Shoes ($129.99)
    - **SKU54321** - Premium Coffee Maker ($79.99)
    - **SKU11111** - Smart Watch ($199.99)
    - **SKU22222** - Yoga Mat ($49.99)
    - **SKU33333** - High Performance Blender ($149.99)
    
    ### 🔧 Technical Architecture
    - **LangGraph** - Agent orchestration with ReAct reasoning
    - **OpenAI GPT-4** - Natural language processing and analysis
    - **Streamlit** - Modern web interface
    - **Plotly** - Interactive visualizations
    - **ChromaDB** - Vector database for RAG (with fallback)
    
    ### 🚀 Getting Started
    1. Use the **🔍 Product Search** page to find products
    2. Go to **📊 Pricing Analysis** to get AI recommendations
    3. Approve changes and track them in **📋 Approved Changes**
    
    ---
    
    **Built with ❤️ using Streamlit and the PriceWise intelligent pricing system.**
    """)
    
    # System status
    st.markdown("### 🖥️ System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Pricing Agent", "✅ Active" if st.session_state.pricing_agent else "❌ Inactive")
    
    with col2:
        st.metric("Product Retriever", "✅ Active" if st.session_state.product_retriever else "❌ Inactive")
    
    with col3:
        api_key_status = "✅ Configured" if os.getenv("OPENAI_API_KEY") else "❌ Missing"
        st.metric("OpenAI API", api_key_status)

if __name__ == "__main__":
    main() 