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
    
    # Create placeholder for nodes
    node_placeholders = {
        "search_planning": st.empty(),
        "search_execution": st.empty(),
        "preprocessing": st.empty(),
        "valuation": st.empty(),
        "results": st.empty()
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
        # NODE 1: Search Planning
        with node_placeholders["search_planning"].container():
            with st.spinner("🔍 **NODE 1: Generating Search Queries...**"):
                time.sleep(0.5)
                st.session_state.current_node = "search_planning"
            st.success("✅ NODE 1: Search Plan Generated")
        
        # NODE 2: Search Execution & Extraction
        with node_placeholders["search_execution"].container():
            with st.spinner("🔍 **NODE 2: Executing Searches & Extracting Data...**"):
                time.sleep(0.5)
                st.session_state.current_node = "search_execution"
            st.success("✅ NODE 2: Searches Completed")
        
        # NODE 3: Preprocessing
        with node_placeholders["preprocessing"].container():
            with st.spinner("🔧 **NODE 3: Preprocessing & Filtering Comparables...**"):
                time.sleep(0.5)
                st.session_state.current_node = "preprocessing"
            st.success("✅ NODE 3: Data Preprocessed")
        
        # NODE 4: Valuation
        with node_placeholders["valuation"].container():
            with st.spinner("💰 **NODE 4: Generating Valuation & Analysis...**"):
                time.sleep(0.5)
                st.session_state.current_node = "valuation"
            st.success("✅ NODE 4: Valuation Complete")
        
        # Run the actual valuation
        graph = RealEstateValuationGraph()
        
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
        
        # RESULTS SECTION
        with node_placeholders["results"].container():
            # Verdict Section - Large and Prominent
            st.markdown("## 📊 VALUATION VERDICT")
            
            vs_asking = valuation_report.get('vs_asking_price', {})
            verdict = vs_asking.get('verdict', 'fair').upper()
            estimated_mid = valuation_report.get('estimated_price_range', {}).get('mid', 0)
            asking = vs_asking.get('asking_price', 0)
            difference = vs_asking.get('difference', 0)
            percentage_diff = vs_asking.get('percentage_diff', 0)
            
            # Determine verdict styling
            verdict_color = "#ff4444"
            verdict_bg = "ffe5e5"
            verdict_icon = "📉"
            if verdict == "UNDERPRICED":
                verdict_color = "#00cc00"
                verdict_bg = "e5ffe5"
                verdict_icon = "📈"
            elif verdict == "FAIR":
                verdict_color = "#ffaa00"
                verdict_bg = "fffae5"
                verdict_icon = "➡️"
            
            # Verdict Card
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                    <div style="background-color: #{verdict_bg}; padding: 2rem; border-radius: 0.5rem; border-left: 8px solid {verdict_color};">
                        <h2 style="color: {verdict_color}; margin: 0;">🎯 {verdict}</h2>
                        <p style="font-size: 1.5rem; color: {verdict_color}; margin: 0.5rem 0;">
                            Asking: <strong>${asking:,.0f}</strong> | Estimated: <strong>${estimated_mid:,.0f}</strong>
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
            price_range = valuation_report.get('estimated_price_range', {})
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Low Estimate", f"${price_range.get('low', 0):,.0f}")
            col2.metric("Mid Estimate", f"${price_range.get('mid', 0):,.0f}", delta=f"{percentage_diff:+.1f}%")
            col3.metric("High Estimate", f"${price_range.get('high', 0):,.0f}")
            col4.metric("Recommended Listing", f"${price_range.get('recommended_listing', 0):,.0f}")
            
            st.markdown("---")
            
            # Comparable Sales Section
            st.markdown("## 🏘️ Comparable Sales Analysis")
            comparable_sales = scraped_data.get('sold_homes', [])
            
            if comparable_sales:
                st.info(f"✅ Found {len(comparable_sales)} comparable sales")
                for i, comp in enumerate(comparable_sales, 1):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric(f"Comp {i}", f"${comp.get('price', 0):,.0f}")
                    col2.metric("Price/sqft", f"${comp.get('price', 0) / max(comp.get('sqft', 1), 1):.2f}")
                    col3.metric("Sqft", f"{comp.get('sqft', 0):,}")
                    col4.metric("Bedrooms", comp.get('bedrooms', 'N/A'))
                    col5.metric("Sale Date", comp.get('date_sold', 'N/A'))
            else:
                st.warning("⚠️ No comparable sales found with sufficient data")
            
            st.markdown("---")
            
            # Market Insights Section
            st.markdown("## 📈 Market Insights")
            market_stats = preprocessed_data.get('market_statistics', {})
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(
                "Avg Price/sqft",
                f"${market_stats.get('avg_price_per_sqft', 0):.2f}"
            )
            col2.metric(
                "Total Sold Homes",
                market_stats.get('total_sold', 0)
            )
            col3.metric(
                "Data Confidence",
                preprocessed_data.get('data_quality', {}).get('quality_score', 0.0)
            )
            col4.metric(
                "Comps Used",
                len(comparable_sales)
            )
            
            st.markdown("---")
            
            # Search Results & Links Section
            st.markdown("## 🔗 Search Results & Links")
            
            # Show query analysis and zip discovery results
            if query_analysis:
                st.subheader("🎯 Query Analysis")
                st.write(f"**Intent:** {query_analysis.get('intent', 'N/A')}")
                st.write(f"**Location:** {query_analysis.get('location', {}).get('value', 'N/A')}")
                
            if zip_discovery:
                st.subheader("� ZIP Codes Discovered")
                st.write(f"**Primary ZIP:** {zip_discovery.get('primary_zip', 'N/A')}")
                nearby_zips = zip_discovery.get('nearby_zips', [])
                if nearby_zips:
                    st.write(f"**Nearby ZIPs:** {', '.join(map(str, nearby_zips[:10]))}")  # Show first 10
            
            # Reasoning Section
            st.markdown("## 📝 Valuation Reasoning")
            reasoning = valuation_report.get('reasoning', {})
            comp_estimate = reasoning.get('comp_based_estimate', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Comp-Based Estimate:**")
                st.write(f"- Method: {comp_estimate.get('method', 'N/A')}")
                st.write(f"- Avg Price/sqft: ${comp_estimate.get('avg_price_per_sqft', 0):.2f}")
                st.write(f"- Calculation: {comp_estimate.get('calculation', 'N/A')}")
                st.write(f"- Comps Used: {len(comp_estimate.get('comps_used', []))}")
            
            with col2:
                st.markdown("**Final Reasoning:**")
                st.write(reasoning.get('final_reasoning', 'N/A'))
            
            st.markdown("---")
            
            # Recommendations Section
            st.markdown("## 💡 Recommendations")
            recommendations = valuation_report.get('recommendations', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Listing Strategy:**")
                st.write(recommendations.get('listing_strategy', 'N/A'))
            
            with col2:
                st.markdown("**Expected Days on Market:**")
                st.write(f"{recommendations.get('expected_days_on_market', 0)} days")
            
            with col3:
                st.markdown("**Overall Confidence:**")
                confidence = preprocessed_data.get('data_quality', {}).get('confidence', 'low').upper()
                st.write(confidence)
            
            st.markdown("---")
            
            # Download Report Button
            st.markdown("## 📥 Export Report")
            report_json = json.dumps(valuation_report, indent=2)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📋 Download JSON Report",
                    data=report_json,
                    file_name=f"valuation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                # Create CSV export
                import pandas as pd
                comp_data = []
                for comp in comparable_sales:
                    comp_data.append({
                        "Address": comp.get('address', 'N/A'),
                        "Price": comp.get('price', 0),
                        "Price/sqft": comp.get('price', 0) / max(comp.get('sqft', 1), 1),
                        "Sqft": comp.get('sqft', 0),
                        "Bedrooms": comp.get('bedrooms', 'N/A'),
                        "Date Sold": comp.get('date_sold', 'N/A'),
                        "ZIP": comp.get('zipcode', 'N/A')
                    })
                
                if comp_data:
                    df = pd.DataFrame(comp_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📊 Download Comparables CSV",
                        data=csv,
                        file_name=f"comparables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

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
