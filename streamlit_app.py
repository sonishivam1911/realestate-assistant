import streamlit as st
import json
import time
from datetime import datetime
from workflow.valuation_graph import RealEstateValuationGraph
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Suppress verbose logs from external libraries
logging.getLogger("ddgs.ddgs").setLevel(logging.WARNING)
logging.getLogger("primp").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Set page config
st.set_page_config(
    page_title="Real Estate Valuation Assistant",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .verdict-overpriced {
        background-color: #ffe5e5;
        border-left-color: #ff4444;
        color: #cc0000;
    }
    .verdict-underpriced {
        background-color: #e5ffe5;
        border-left-color: #00cc00;
        color: #006600;
    }
    .verdict-fair {
        background-color: #fffae5;
        border-left-color: #ffaa00;
        color: #884400;
    }
    .comparable-item {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 0.5rem;
    }
    .node-progress {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .node-completed {
        background-color: #e5ffe5;
        border-left: 4px solid #00cc00;
    }
    .node-active {
        background-color: #fff8e5;
        border-left: 4px solid #ffaa00;
    }
    .search-link {
        display: inline-block;
        background-color: #1f77b4;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        text-decoration: none;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🏠 Real Estate Property Valuation Assistant")
st.markdown("---")

# Sidebar for input
with st.sidebar:
    st.header("📋 Property Details")
    
    address = st.text_input(
        "Address",
        value="123 Main Street, Austin, TX 78701",
        help="Full property address"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        bedrooms = st.number_input("Bedrooms", min_value=1, max_value=10, value=3)
        sqft = st.number_input("Square Footage", min_value=500, max_value=10000, value=1800)
    
    with col2:
        bathrooms = st.number_input("Bathrooms", min_value=1, max_value=10, value=2)
        asking_price = st.number_input("Asking Price ($)", min_value=50000, max_value=10000000, value=450000, step=10000)
    
    property_type = st.selectbox(
        "Property Type",
        ["Single Family", "Condo", "Townhouse", "Multi-Family"],
        index=0
    )
    
    year_built = st.number_input("Year Built", min_value=1900, max_value=2025, value=2010)
    
    st.markdown("---")
    run_valuation = st.button("🚀 Run Valuation", use_container_width=True, type="primary")

# Main content area
if run_valuation:
    property_details = {
        "address": address,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "sqft": sqft,
        "asking_price": asking_price,
        "property_type": property_type,
        "year_built": year_built
    }
    
    # Show initial property info
    with st.container():
        st.subheader("📍 Property Information")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Address", address.split(",")[0])
        col2.metric("Bedrooms", f"{bedrooms} bed | {bathrooms} bath")
        col3.metric("Size", f"{sqft:,} sqft")
        col4.metric("Asking Price", f"${asking_price:,}")
    
    st.markdown("---")
    st.subheader("⚙️ Valuation Progress")
    
    # Initialize session state for tracking
    if 'current_node' not in st.session_state:
        st.session_state.current_node = None
    
    try:
        # Node display mapping
        node_config = {
            "query_analysis": {
                "display_name": "Query Analysis",
                "emoji": "🔍",
                "description": "Analyzing your search query..."
            },
            "zip_discovery": {
                "display_name": "ZIP Discovery",
                "emoji": "📍",
                "description": "Discovering nearby ZIP codes..."
            },
            "scraping": {
                "display_name": "Zillow Scraping",
                "emoji": "🕷️",
                "description": "Scraping property data from Zillow..."
            },
            "preprocessing": {
                "display_name": "Data Preprocessing",
                "emoji": "🔧",
                "description": "Filtering and validating data..."
            },
            "valuation": {
                "display_name": "Valuation",
                "emoji": "💰",
                "description": "Generating final valuation..."
            }
        }
        
        # Track completed nodes
        completed_nodes = set()
        
        # Show all nodes with initial states
        node_status_containers = {}
        for node_key in ["query_analysis", "zip_discovery", "scraping", "preprocessing", "valuation"]:
            node_status_containers[node_key] = st.empty()
            with node_status_containers[node_key].container():
                st.markdown(f"""
                    <div style="padding: 1rem; background-color: #f0f2f6; border-radius: 0.5rem; border-left: 4px solid #888; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.2rem;">{node_config[node_key]['emoji']} {node_config[node_key]['display_name']}</span>
                        <span style="float: right; color: #888;">⏳ Pending...</span>
                    </div>
                """, unsafe_allow_html=True)
        
        # Create a custom wrapper to intercept workflow execution
        class NodeTracker:
            def __init__(self):
                self.nodes_completed = set()
            
            def update_node_status(self, node_name, status="active"):
                """Update UI for a specific node"""
                if status == "active":
                    icon = "⏳"
                    bg_color = "#fff8e5"
                    border_color = "#ffaa00"
                    status_text = "Processing..."
                elif status == "completed":
                    icon = "✅"
                    bg_color = "#e5ffe5"
                    border_color = "#00cc00"
                    status_text = "Completed"
                else:
                    icon = "⏳"
                    bg_color = "#f0f2f6"
                    border_color = "#888"
                    status_text = "Pending..."
                
                config = node_config.get(node_name, {})
                with node_status_containers[node_name].container():
                    st.markdown(f"""
                        <div style="padding: 1rem; background-color: {bg_color}; border-radius: 0.5rem; border-left: 4px solid {border_color}; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.2rem;">{icon} {config.get('display_name', node_name)}</span>
                            <span style="float: right; font-size: 0.9rem; color: {border_color};">{status_text}</span>
                            <br/>
                            <span style="font-size: 0.85rem; color: #666;">{config.get('description', '')}</span>
                        </div>
                    """, unsafe_allow_html=True)
        
        tracker = NodeTracker()
        
        # Run the actual valuation
        graph = RealEstateValuationGraph()
        
        # Intercept node updates by monkey-patching (we'll show progress)
        original_node_funcs = {
            "query_analysis": graph._node_query_analysis,
            "zip_discovery": graph._node_zip_discovery,
            "scraping": graph._node_scraping,
            "preprocessing": graph._node_preprocessing,
            "valuation": graph._node_valuation
        }
        
        # Wrap each node function to update UI
        def make_tracked_node(node_name, original_func):
            def tracked_node(state):
                tracker.update_node_status(node_name, "active")
                result = original_func(state)
                tracker.update_node_status(node_name, "completed")
                return result
            return tracked_node
        
        for node_name, original_func in original_node_funcs.items():
            setattr(graph, f"_node_{node_name}", make_tracked_node(node_name, original_func))
        
        # Rebuild graph with tracked nodes
        graph.graph = graph._build_graph()
        
        # Create a user query from the address
        user_query = f"Value my property at {address}"
        
        # Run with proper parameters
        result = graph.run(user_query, property_details)
        
        # Extract results from workflow state
        valuation_report = result.get('valuation_report', {})
        scraped_data = result.get('scraped_data', {})
        preprocessed_data = result.get('preprocessed_data', {})
        query_analysis = result.get('query_analysis', {})
        zip_discovery = result.get('zip_discovery', {})
        
        st.markdown("---")
        
        # RESULTS SECTION - Display valuation results properly
        st.markdown("## 🎉 VALUATION COMPLETE!")
        
        # Extract valuation data with proper keys
        valuation_report = result.get('valuation_report', {})
        estimated_value = valuation_report.get('estimated_value', {})
        estimated_mid = estimated_value.get('mid', 0)
        estimated_low = estimated_value.get('low', 0)
        estimated_high = estimated_value.get('high', 0)
        
        # Calculate verdict
        if estimated_mid > 0 and asking_price > 0:
            difference = estimated_mid - asking_price
            percentage_diff = (difference / asking_price) * 100
            
            if percentage_diff > 10:
                verdict = "UNDERPRICED"
                verdict_color = "#00cc00"
                verdict_bg = "e5ffe5"
                verdict_icon = "📈"
            elif percentage_diff < -10:
                verdict = "OVERPRICED"
                verdict_color = "#ff4444"
                verdict_bg = "ffe5e5"
                verdict_icon = "📉"
            else:
                verdict = "FAIR"
                verdict_color = "#ffaa00"
                verdict_bg = "fffae5"
                verdict_icon = "➡️"
        else:
            verdict = "FAIR"
            verdict_color = "#ffaa00"
            verdict_bg = "fffae5"
            verdict_icon = "➡️"
            difference = 0
            percentage_diff = 0
        
        # Verdict Card - Large and Prominent
        st.markdown("## 📊 VALUATION VERDICT")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
                <div style="background-color: #{verdict_bg}; padding: 2rem; border-radius: 0.5rem; border-left: 8px solid {verdict_color};">
                    <h2 style="color: {verdict_color}; margin: 0;">🎯 {verdict}</h2>
                    <p style="font-size: 1.5rem; color: {verdict_color}; margin: 0.5rem 0;">
                        Asking: <strong>${asking_price:,.0f}</strong> | Estimated: <strong>${estimated_mid:,.0f}</strong>
                    </p>
                    <p style="font-size: 1.2rem; color: {verdict_color}; margin: 0;">
                        Difference: <strong>${difference:+,.0f} ({percentage_diff:+.1f}%)</strong>
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: center; font-size: 3rem;">
                    {verdict_icon}
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Price Estimate Section
        st.markdown("## 💰 Estimated Price Range")
        col1, col2, col3, col4 = st.columns(4)
        estimated_low = float(estimated_low) if estimated_low else 0
        estimated_mid = float(estimated_mid) if estimated_mid else 0
        estimated_high = float(estimated_high) if estimated_high else 0
        col1.metric("Low Estimate", f"${estimated_low:,.0f}")
        col2.metric("Mid Estimate", f"${estimated_mid:,.0f}", delta=f"{percentage_diff:+.1f}%")
        col3.metric("High Estimate", f"${estimated_high:,.0f}")
        recommended = estimated_value.get('recommended_listing_price', estimated_mid)
        recommended = float(recommended) if recommended else estimated_mid
        col4.metric("Recommended Listing", f"${recommended:,.0f}")
        
        st.markdown("---")
        
        # Market Analysis
        st.markdown("## 📈 Market Analysis")
        market_analysis = valuation_report.get('market_analysis', {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Market Trend", market_analysis.get('trend', 'Unknown').title())
        col2.metric("Inventory Status", market_analysis.get('inventory_status', 'Unknown').title())
        col3.metric("Price Trend (6mo)", market_analysis.get('price_trend_6mo', '+0%'))
        
        st.markdown("---")
        
        # Data Quality & Stats
        st.markdown("## 📊 Valuation Data Quality")
        preprocessed_data = result.get('preprocessed_data', {})
        data_quality = preprocessed_data.get('data_quality', {})
        scraped_data = result.get('scraped_data', {})
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Quality Score", f"{data_quality.get('quality_score', 0)*100:.0f}%")
        col2.metric("Sold Properties Used", data_quality.get('total_sold_kept', 0))
        col3.metric("For-Sale Properties", data_quality.get('total_for_sale_kept', 0))
        col4.metric("Total Comparables", len(scraped_data.get('sold_homes', [])))
        
        st.markdown("---")
        
        # Confidence Section
        st.markdown("## 📊 Valuation Confidence")
        confidence = valuation_report.get('confidence', {})
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Overall Confidence", confidence.get('overall_confidence', 'Unknown').title())
            st.metric("Confidence Score", f"{confidence.get('score', 0):.2f}")
            
            if confidence.get('factors'):
                st.markdown("**Positive Factors:**")
                for factor in confidence['factors'][:3]:
                    st.write(f"✅ {factor}")
        
        with col2:
            if confidence.get('concerns'):
                st.markdown("**Concerns:**")
                for concern in confidence['concerns'][:3]:
                    st.write(f"⚠️ {concern}")
        
        st.markdown("---")
        
        # Comparable Analysis
        st.markdown("## 🏘️ Top Comparable Properties")
        comparable_sales = scraped_data.get('sold_homes', [])
        
        if comparable_sales:
            st.markdown(f"**Found {len(comparable_sales)} comparable sales**")
            
            # Show top 5 comparables
            for i, comp in enumerate(comparable_sales[:5], 1):
                with st.expander(f"#{i}: {comp.get('address', 'Unknown Address')}"):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    price = comp.get('price') or 0
                    sqft = comp.get('living_area_sqft') or 1
                    price_per_sqft = price / max(sqft, 1) if price and sqft else 0
                    
                    col1.metric("Sale Price", f"${price:,.0f}")
                    col2.metric("Price/sqft", f"${price_per_sqft:.2f}")
                    col3.metric("Sqft", f"{sqft:,}")
                    col4.metric("Beds/Baths", f"{comp.get('bedrooms', 0)}/{comp.get('bathrooms', 0)}")
                    col5.metric("Sale Date", comp.get('date_sold', 'Recent'))
        else:
            st.warning("⚠️ No comparable sales data available")
        
        st.markdown("---")
        
        # Recommendations
        st.markdown("## 💡 Recommendations")
        recommendations = valuation_report.get('recommendations', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            if recommendations.get('for_sellers'):
                st.markdown("**For Sellers:**")
                for rec in recommendations['for_sellers'][:2]:
                    st.write(f"• {rec}")
        
        with col2:
            if recommendations.get('for_buyers'):
                st.markdown("**For Buyers:**")
                for rec in recommendations['for_buyers'][:2]:
                    st.write(f"• {rec}")
        
        st.markdown("---")
        
        # Export Options
        st.markdown("## 📥 Export Report")
        
        col1, col2 = st.columns(2)
        with col1:
            report_json = json.dumps(valuation_report, indent=2)
            st.download_button(
                label="📋 Download JSON Report",
                data=report_json,
                file_name=f"valuation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # CSV export for comparables
            if comparable_sales:
                comp_data = []
                for comp in comparable_sales[:20]:
                    price = comp.get('price') or 0
                    sqft = comp.get('living_area_sqft') or 1
                    price = float(price) if price else 0
                    sqft = float(sqft) if sqft else 1
                    comp_data.append({
                        "Address": comp.get('address', 'N/A'),
                        "Price": f"${price:,.0f}",
                        "Price/sqft": f"${price/max(sqft, 1):.2f}",
                        "Sqft": f"{sqft:,}",
                        "Bedrooms": comp.get('bedrooms', 'N/A'),
                        "Bathrooms": comp.get('bathrooms', 'N/A'),
                        "Sale Date": comp.get('date_sold', 'N/A')
                    })
                
                import pandas as pd
                df = pd.DataFrame(comp_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📊 Download Comparables CSV",
                    data=csv,
                    file_name=f"comparables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        st.markdown("---")
        st.success("✅ Valuation Report Complete! You can download your reports above.")
    
    except Exception as e:
        st.error(f"❌ Error during valuation: {str(e)}")
        st.write("Please check your input and try again.")
        import traceback
        st.write(traceback.format_exc())

else:
    # Landing page
    st.markdown("""
    ## Welcome to Real Estate Valuation Assistant 🏠
    
    This AI-powered tool analyzes comparable sales and market data to provide accurate property valuations.
    
    ### Features:
    - 🔍 **Intelligent Search**: Searches for comparable properties using DuckDuckGo
    - 🤖 **AI Data Extraction**: Uses LLM to intelligently extract property data from search results
    - 📊 **Market Analysis**: Analyzes comparable sales and market trends
    - 💰 **Price Estimation**: Provides estimated price range with confidence levels
    - 🎯 **Valuation Verdict**: Determines if property is underpriced, fair, or overpriced
    - 🔗 **Source Links**: Shows all search results with direct links for verification
    - 📈 **Comet ML Logging**: All LLM calls, searches, and workflow steps logged to Comet ML
    
    ### How It Works:
    1. **Enter Property Details** - Address, size, bedrooms, asking price
    2. **Run Valuation** - System searches for comparables and analyzes market data
    3. **Review Results** - Get estimated price range, comparable sales, and verdict
    4. **Export Report** - Download detailed valuation report
    5. **View Logs** - All workflow steps logged to Comet ML for monitoring
    
    ---
    
    📝 **Enter your property details in the sidebar and click "Run Valuation" to get started!**
    """)
    
    # Example card
    st.info("""
    💡 **Example:** A 3-bedroom, 1,800 sqft home in Austin, TX 78701 asking $450,000
    """)
    
    # Comet ML Info
    st.markdown("---")
    st.markdown("### 📊 LangSmith Integration")
    
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    if langsmith_api_key:
        st.success("✅ LangSmith is configured and will log all workflow steps and LLM calls")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Project:** {os.getenv('LANGSMITH_PROJECT', 'realestate-valuation')}")
        with col2:
            st.markdown(f"**API Key:** Configured")
        
        st.markdown("""
        **Tracked with @traceable Decorator:**
        - 🏗️ build_valuation_workflow - Workflow construction
        - 🔍 search_planning_node - Query generation
        - � search_execution_node - Web searches + LLM extraction
        - 🔧 preprocessing_node - Data filtering & validation
        - 💰 valuation_node - Valuation generation
        - 🚀 run_valuation_workflow - Complete workflow execution
        
        All LLM calls and node executions are automatically traced!
        """)
    else:
        st.warning("⚠️ LangSmith API key not configured. Set LANGSMITH_API_KEY environment variable to enable tracing.")
