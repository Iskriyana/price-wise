"""
Streamlit UI for Iteration 1: RAG-powered Pricing Agent

This provides a user-friendly web interface for pricing analysts to interact
with the RAG-powered pricing recommendation system.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
import sys
import os
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import PricingQuery, PricingRecommendation
from src.pricing_agent import PricingRAGAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="PriceWise AI - Pricing Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .metric-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin: 0.5rem 0;
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

def initialize_agent():
    """Initialize the pricing agent"""
    try:
        with st.spinner("🚀 Initializing Pricing Agent..."):
            agent = PricingRAGAgent()
            agent.initialize()
            st.session_state.agent = agent
            st.session_state.agent_initialized = True
            st.success("✅ Pricing Agent initialized successfully!")
            return True
    except Exception as e:
        st.error(f"❌ Failed to initialize agent: {str(e)}")
        return False

def display_system_status():
    """Display system status in sidebar"""
    st.sidebar.subheader("🖥️ System Status")
    
    if st.session_state.agent_initialized and st.session_state.agent:
        status = st.session_state.agent.get_agent_status()
        
        # Status indicators
        st.sidebar.success("🟢 Agent: Ready")
        
        if status.get('has_openai_key'):
            st.sidebar.success("🟢 OpenAI: Connected")
        else:
            st.sidebar.warning("🟡 OpenAI: Fallback Mode")
        
        if status.get('retrieval_method') == 'vector_store':
            st.sidebar.success("🟢 Vector Store: Active")
        else:
            st.sidebar.warning("🟡 Retrieval: Text-based Fallback")
        
        # Data summary
        if status.get('data_summary'):
            data_summary = status['data_summary']
            st.sidebar.markdown("**📊 Data Overview:**")
            st.sidebar.write(f"• Products: {data_summary.get('total_products', 0)}")
            st.sidebar.write(f"• Brands: {len(data_summary.get('brands', []))}")
            st.sidebar.write(f"• Categories: {len(data_summary.get('categories', []))}")
            
            price_range = data_summary.get('price_range', {})
            if price_range:
                st.sidebar.write(f"• Price Range: ${price_range.get('min', 0):.2f} - ${price_range.get('max', 0):.2f}")
    else:
        st.sidebar.error("🔴 Agent: Not Initialized")

def create_product_overview():
    """Create product overview dashboard"""
    if not st.session_state.agent_initialized:
        return
    
    try:
        # Get data summary
        status = st.session_state.agent.get_agent_status()
        data_summary = status.get('data_summary', {})
        
        if not data_summary:
            st.warning("No product data available")
            return
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Products", 
                data_summary.get('total_products', 0),
                help="Total number of products in the system"
            )
        
        with col2:
            st.metric(
                "Brands", 
                len(data_summary.get('brands', [])),
                help="Number of unique brands"
            )
        
        with col3:
            st.metric(
                "Categories", 
                len(data_summary.get('categories', [])),
                help="Number of product categories"
            )
        
        with col4:
            price_range = data_summary.get('price_range', {})
            avg_price = price_range.get('avg', 0)
            st.metric(
                "Avg Price", 
                f"${avg_price:.2f}",
                help="Average product price"
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Brand distribution
            brands = data_summary.get('brands', [])[:10]  # Top 10 brands
            if brands:
                brand_df = pd.DataFrame({'Brand': brands, 'Count': [1] * len(brands)})
                fig = px.bar(brand_df, x='Brand', y='Count', title="Available Brands")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Category distribution
            categories = data_summary.get('categories', [])[:10]  # Top 10 categories
            if categories:
                category_df = pd.DataFrame({'Category': categories, 'Count': [1] * len(categories)})
                fig = px.pie(category_df, values='Count', names='Category', title="Product Categories")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error creating overview: {str(e)}")

def display_recommendation(recommendation: PricingRecommendation):
    """Display pricing recommendation in a formatted way"""
    
    # Main recommendation
    st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
    st.subheader("💡 Recommendation")
    st.write(recommendation.recommendation)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if recommendation.recommended_price:
            st.metric("Recommended Price", f"${recommendation.recommended_price:.2f}")
        else:
            st.metric("Recommended Price", "See analysis")
    
    with col2:
        confidence_pct = recommendation.confidence_score * 100
        st.metric("Confidence", f"{confidence_pct:.0f}%")
    
    with col3:
        approval_level = recommendation.approval_threshold or "analyst"
        st.metric("Approval Required", approval_level.title())
    
    with col4:
        products_analyzed = len(recommendation.product_info)
        st.metric("Products Analyzed", products_analyzed)
    
    # Detailed analysis
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Detailed Analysis")
        st.text_area("Reasoning", recommendation.reasoning, height=200, disabled=True)
    
    with col2:
        st.subheader("📊 Market Context")
        st.text_area("Market Analysis", recommendation.market_context, height=200, disabled=True)
    
    # Product details
    if recommendation.product_info:
        st.subheader("🏷️ Product Details")
        
        product_data = []
        for product in recommendation.product_info[:5]:  # Show top 5 products
            current_margin = ((product.current_price - product.cost_price) / product.current_price * 100) if product.current_price > 0 else 0
            avg_competitor_price = sum(product.competitor_prices) / len(product.competitor_prices) if product.competitor_prices else 0
            recent_sales = sum(product.hourly_sales) if product.hourly_sales else 0
            
            product_data.append({
                "SKU": product.item_id,
                "Product": product.item_name,
                "Current Price": f"${product.current_price:.2f}",
                "Cost": f"${product.cost_price:.2f}",
                "Current Margin": f"{current_margin:.1f}%",
                "Target Margin": f"{product.target_margin_percent:.1f}%",
                "Avg Competitor": f"${avg_competitor_price:.2f}" if avg_competitor_price > 0 else "N/A",
                "Stock": product.stock_level,
                "Recent Sales": recent_sales
            })
        
        if product_data:
            df = pd.DataFrame(product_data)
            st.dataframe(df, use_container_width=True)

def create_example_queries():
    """Create example queries for users"""
    st.subheader("💡 Example Queries")
    
    examples = [
        {
            "title": "🎯 Specific Product Analysis",
            "query": "What is the recommended price for Product SKU APP10000 given that our main competitor lowered their price by 10% yesterday?",
            "context": "Competitor price reduction scenario",
            "product_ids": ["APP10000"]
        },
        {
            "title": "🏷️ Brand Strategy",
            "query": "Should we increase prices for Adidas T-shirts to improve our profit margin?",
            "context": "Margin optimization for brand category",
            "product_ids": []
        },
        {
            "title": "⚖️ Competitive Analysis",
            "query": "Which Nike products are overpriced compared to competitors?",
            "context": "Competitive pricing analysis",
            "product_ids": []
        },
        {
            "title": "📦 Inventory Management",
            "query": "What pricing strategy should we use for products with high inventory levels?",
            "context": "Inventory management pricing",
            "product_ids": []
        },
        {
            "title": "🌍 Market-Based Pricing",
            "query": "Recommend pricing for Under Armour Socks (APP10005) considering current market conditions",
            "context": "Market-based pricing recommendation",
            "product_ids": ["APP10005"]
        }
    ]
    
    for i, example in enumerate(examples):
        with st.expander(example["title"]):
            st.write(f"**Query:** {example['query']}")
            st.write(f"**Context:** {example['context']}")
            if example['product_ids']:
                st.write(f"**Product IDs:** {', '.join(example['product_ids'])}")
            
            if st.button(f"Use This Query", key=f"example_{i}"):
                st.session_state.example_query = example['query']
                st.session_state.example_context = example['context']
                st.session_state.example_product_ids = ', '.join(example['product_ids'])
                st.rerun()

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>💰 PriceWise AI - Iteration 1</h1>
        <p>RAG-powered Pricing Analyst Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize agent if needed
    if not st.session_state.agent_initialized:
        st.info("🚀 Welcome to PriceWise AI! Click below to initialize the pricing agent.")
        if st.button("Initialize Pricing Agent", type="primary"):
            initialize_agent()
        
        st.markdown("---")
        st.subheader("📋 About This System")
        st.write("""
        **PriceWise AI** is a RAG-powered pricing analyst assistant that helps you:
        - 🔍 Analyze product pricing strategies
        - 📊 Compare against competitor prices
        - 📈 Optimize profit margins
        - 📦 Consider inventory levels
        - ✅ Generate approval-ready recommendations
        """)
        return
    
    # Sidebar
    display_system_status()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Query Assistant", "📊 Product Overview", "📚 Query History"])
    
    with tab1:
        st.subheader("🤖 Ask the Pricing Agent")
        
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
                "Your Pricing Question",
                value=default_query,
                placeholder="e.g., Should we increase the price of Nike sneakers given current market conditions?",
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
            
            submitted = st.form_submit_button("🔍 Analyze Pricing", type="primary")
        
        if submitted and query.strip():
            try:
                # Parse product IDs
                product_id_list = [pid.strip() for pid in product_ids.split(',') if pid.strip()] if product_ids else None
                
                # Create query object
                pricing_query = PricingQuery(
                    query=query,
                    context=context if context else None,
                    product_ids=product_id_list
                )
                
                # Process query
                with st.spinner("🤖 Analyzing your pricing question..."):
                    recommendation = st.session_state.agent.process_query(pricing_query)
                
                # Store in history
                st.session_state.query_history.append({
                    'timestamp': datetime.now(),
                    'query': query,
                    'context': context,
                    'product_ids': product_ids,
                    'recommendation': recommendation
                })
                
                # Display recommendation
                display_recommendation(recommendation)
                
            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
        
        elif submitted:
            st.warning("⚠️ Please enter a pricing question.")
        
        # Examples section
        st.markdown("---")
        create_example_queries()
    
    with tab2:
        st.subheader("📊 Product Overview")
        create_product_overview()
    
    with tab3:
        st.subheader("📚 Query History")
        
        if st.session_state.query_history:
            for i, entry in enumerate(reversed(st.session_state.query_history[-10:])):  # Show last 10
                with st.expander(f"Query {len(st.session_state.query_history) - i}: {entry['query'][:50]}..."):
                    st.write(f"**Timestamp:** {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Query:** {entry['query']}")
                    if entry['context']:
                        st.write(f"**Context:** {entry['context']}")
                    if entry['product_ids']:
                        st.write(f"**Product IDs:** {entry['product_ids']}")
                    
                    st.markdown("**Recommendation:**")
                    st.write(entry['recommendation'].recommendation)
                    
                    if entry['recommendation'].recommended_price:
                        st.write(f"**Suggested Price:** ${entry['recommendation'].recommended_price:.2f}")
                    
                    confidence_pct = entry['recommendation'].confidence_score * 100
                    st.write(f"**Confidence:** {confidence_pct:.0f}%")
            
            if st.button("🗑️ Clear History"):
                st.session_state.query_history = []
                st.rerun()
        else:
            st.info("📝 No queries yet. Start by asking a pricing question in the Query Assistant tab.")

if __name__ == "__main__":
    main() 