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
    page_title="Test your Consumer Market Analysis against my multi agent real estate system",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    /* Main layout */
    .main {
        padding: 2rem;
    }
    
    /* Unified Progress Loader */
    @keyframes progressFill {
        0% { width: 0%; }
        100% { width: 100%; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    @keyframes checkmark {
        0% { transform: scale(0) rotate(-45deg); opacity: 0; }
        50% { transform: scale(1.2) rotate(10deg); }
        100% { transform: scale(1) rotate(0deg); opacity: 1; }
    }
    
    /* Main progress container */
    .unified-progress-container {
        width: 100%;
        padding: 2rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f6 100%);
        border-radius: 16px;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #e0e0e0;
    }
    
    /* Progress title with current step */
    .progress-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .progress-emoji {
        font-size: 1.6rem;
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Progress bar background */
    .progress-bar-background {
        width: 100%;
        height: 8px;
        background-color: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        margin: 1.5rem 0 1rem 0;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06);
    }
    
    /* Progress bar fill */
    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #00cc00 0%, #00ff00 50%, #00cc00 100%);
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 204, 0, 0.4);
        animation: shimmer 2s ease-in-out infinite;
        transition: width 0.3s ease;
    }
    
    /* Step indicators */
    .step-indicators {
        display: flex;
        justify-content: space-between;
        margin-top: 1rem;
        gap: 0.5rem;
    }
    
    .step-indicator {
        flex: 1;
        height: 4px;
        background-color: #ddd;
        border-radius: 2px;
        transition: all 0.3s ease;
    }
    
    .step-indicator.completed {
        background-color: #00cc00;
        box-shadow: 0 0 6px rgba(0, 204, 0, 0.3);
    }
    
    .step-indicator.active {
        background-color: #ffaa00;
        box-shadow: 0 0 6px rgba(255, 170, 0, 0.3);
        animation: pulse 1s ease-in-out infinite;
    }
    
    .step-indicator.pending {
        background-color: #ccc;
    }
    
    /* Step labels */
    .step-labels {
        display: flex;
        justify-content: space-between;
        margin-top: 0.8rem;
        font-size: 0.75rem;
        font-weight: 500;
        color: #666;
        text-align: center;
    }
    
    .step-label {
        flex: 1;
        padding: 0 0.25rem;
    }
    
    .step-label.active {
        color: #ffaa00;
        font-weight: 600;
    }
    
    .step-label.completed {
        color: #00cc00;
        font-weight: 600;
    }
    
    /* Status message */
    .progress-status {
        font-size: 0.9rem;
        color: #666;
        margin-top: 1rem;
        text-align: center;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    
    .progress-status.complete {
        color: #00cc00;
        font-weight: 600;
    }
    
    /* Other card styles */
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
        value="199 Hyde Park, Somerset, NJ 08873",
        help="Full property address"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        bedrooms = st.number_input("Bedrooms", min_value=1, max_value=10, value=2)
        sqft = st.number_input("Square Footage", min_value=500, max_value=10000, value=1400)
    
    with col2:
        bathrooms = st.number_input("Bathrooms", min_value=1, max_value=10, value=3)
        asking_price = st.number_input("Asking Price ($)", min_value=50000, max_value=10000000, value=350000, step=10000)
    
    property_type = st.selectbox(
        "Property Type",
        ["Single Family", "Condo", "Townhouse", "Multi-Family"],
        index=2
    )
    
    year_built = st.number_input("Year Built", min_value=1900, max_value=2025, value=1986)
    
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
    
    # Create filters dictionary to pass to Node 0
    # Use property details as filters (with one less bed/bath for search)
    filters = {
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "property_type": property_type.lower(),
        "min_sqft": None,
        "max_sqft": None,
        "year_built": year_built
    }
    
    # Show initial property info
    with st.container():
        st.subheader("Property Information")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Address", address.split(",")[0])
        col2.metric("Bedrooms", f"{bedrooms} bed | {bathrooms} bath")
        col3.metric("Size", f"{sqft:,} sqft")
        col4.metric("Asking Price", f"${asking_price:,}")
    
    st.markdown("---")
    st.subheader("Valuation Progress")
    
    # Simple progress tracking with Streamlit's built-in components
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Node configuration - simple and clean
    nodes_list = ["query_analysis", "zip_discovery", "scraping", "preprocessing", "valuation"]
    node_config = {
        "query_analysis": {"emoji": "", "name": "Query Analysis"},
        "zip_discovery": {"emoji": "", "name": "ZIP Discovery"},
        "scraping": {"emoji": "", "name": "Scraping Zillow"},
        "preprocessing": {"emoji": "", "name": "Processing Data"},
        "valuation": {"emoji": "", "name": "Final Valuation"}
    }
    
    # Simple progress tracker
    class SimpleProgressTracker:
        def __init__(self):
            self.completed = []
            self.current = None
        
        def update(self, node_name):
            self.current = node_name
            name = node_config[node_name]["name"]
            
            # Show current progress
            with progress_placeholder.container():
                # Display nodes as a simple chain
                nodes_display = " → ".join([
                    f"{'✓' if n in self.completed else '●' if n == node_name else '○'} {node_config[n]['name']}"
                    for n in nodes_list
                ])
                st.write(nodes_display)
            
            with status_placeholder.container():
                st.info(f"Processing: **{name}**")
        
        def mark_complete(self, node_name):
            if node_name not in self.completed:
                self.completed.append(node_name)
    
    tracker = SimpleProgressTracker()
    
    # Add logging to capture all output
    import io
    import sys
    
    log_capture = io.StringIO()
    
    try:
        # Run the actual valuation
        graph = RealEstateValuationGraph()
        
        # Create a user query from the address
        user_query = f"Value my property at {address}"
        
        # Simple node wrapper to update progress
        def update_on_node(node_name):
            """Update progress when a node starts"""
            tracker.update(node_name)
        
        # Run with proper parameters
        result = graph.run(
            user_query=user_query,
            target_property=property_details,
            filters=filters
        )
        
        # Extract results from workflow state
        valuation_report = result.get('valuation_report', {})
        scraped_data = result.get('scraped_data', {})
        preprocessed_data = result.get('preprocessed_data', {})
        query_analysis = result.get('query_analysis', {})
        zip_discovery = result.get('zip_discovery', {})
        
        st.markdown("---")
        
        # RESULTS SECTION - Display valuation results properly
        st.markdown("## VALUATION COMPLETE")
        
        # Extract valuation data from the new structure
        # valuation_report IS the action_input (agent returns it directly)
        analysis_summary = valuation_report.get('analysis_summary', {})
        why_this_price = valuation_report.get('why_this_price', '')
        
        # Debug: Show what we got
        print(f"\n📊 Valuation Report Keys: {list(valuation_report.keys())}")
        print(f"📊 Analysis Summary Keys: {list(analysis_summary.keys())}")
        print(f"📊 Raw why_this_price: {repr(why_this_price)}")
        
        # Parse the analysis summary
        estimated_value_str = str(analysis_summary.get('estimated_value', '$0')).replace('$', '').replace(',', '')
        confidence_level = analysis_summary.get('confidence_level', 'unknown')
        confidence_score = float(analysis_summary.get('confidence_score', 0))
        verdict = str(analysis_summary.get('verdict', 'fairly_priced')).upper()
        variance_percent_str = str(analysis_summary.get('variance_percent', '0%')).replace('%', '').replace('±', '')
        asking_price_str = str(analysis_summary.get('asking_price', '$0')).replace('$', '').replace(',', '')
        comps_used = analysis_summary.get('comparable_properties_used', 0)
        
        # Convert to numbers
        try:
            estimated_mid = float(estimated_value_str) if estimated_value_str else 0
            asking_price_num = float(asking_price_str) if asking_price_str else 0
            variance_percent = float(variance_percent_str) if variance_percent_str else 0
        except ValueError as e:
            print(f"❌ Conversion error: {e}")
            estimated_mid = 0
            asking_price_num = 0
            variance_percent = 0
        
        # Determine color and icon based on verdict
        if verdict == "OVERPRICED":
            verdict_color = "#ff4444"
            verdict_bg = "ffe5e5"
            verdict_icon = "📉"
        elif verdict == "UNDERPRICED":
            verdict_color = "#00cc00"
            verdict_bg = "e5ffe5"
            verdict_icon = "📈"
        else:
            verdict_color = "#ffaa00"
            verdict_bg = "fffae5"
            verdict_icon = "➡️"
        
        # Verdict Card - Large and Prominent
        st.markdown("## VALUATION VERDICT")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
                <div style="background-color: #{verdict_bg}; padding: 2rem; border-radius: 0.5rem; border-left: 8px solid {verdict_color};">
                    <h2 style="color: {verdict_color}; margin: 0;">{verdict}</h2>
                    <p style="font-size: 1.5rem; color: {verdict_color}; margin: 0.5rem 0;">
                        Asking: <strong>${asking_price_num:,.0f}</strong> | Estimated: <strong>${estimated_mid:,.0f}</strong>
                    </p>
                    <p style="font-size: 1.2rem; color: {verdict_color}; margin: 0;">
                        Variance: <strong>{variance_percent:+.1f}%</strong>
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: center; font-size: 3rem;">
                    {verdict}
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ✨ NEW: EXECUTIVE SUMMARY - Why this valuation
        st.markdown("## Why This Valuation?")
        # Display as raw text - no markdown processing
        st.text(why_this_price if why_this_price else "No summary available")
        
        st.markdown("---")
        
        # Confidence & Summary Section
        st.markdown("## Valuation Confidence & Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Confidence Level", confidence_level.title())
        col2.metric("Confidence Score", f"{confidence_score:.2f}")
        col3.metric("Comparables Used", comps_used)
        
        st.markdown("---")
        
        # Price Estimate
        st.markdown("## Price Estimate")
        col1, col2 = st.columns(2)
        col1.metric("Estimated Value", f"${estimated_mid:,.0f}")
        col2.metric("Asking Price", f"${asking_price_num:,.0f}")
        
        st.markdown("---")
        
        # Comparable Analysis - Show top 10 comparables used for valuation
        st.markdown("## Comparable Properties Used")
        
        preprocessed_data = result.get('preprocessed_data', {})
        sold_homes = preprocessed_data.get('filtered_sold_homes', [])[:10]
        for_sale_homes = preprocessed_data.get('filtered_for_sale_homes', [])[:10]
        
        all_comparables = sold_homes if sold_homes else for_sale_homes
        
        if all_comparables:
            st.markdown(f"**Found {len(all_comparables)} Comparable Properties**")
            
            for i, comp in enumerate(all_comparables, 1):
                address = comp.get('address', 'Unknown Address')
                price = comp.get('price', 0)
                sqft = comp.get('living_area_sqft', 0)
                ppsf = comp.get('price_per_sqft', 0)
                beds = comp.get('bedrooms', 0)
                baths = comp.get('bathrooms', 0)
                similarity = comp.get('similarity_score', 0)
                status = comp.get('home_status', 'unknown')
                zillow_url = comp.get('url', '')
                
                if similarity > 0.85:
                    expander_title = f"#{i}: {address[:50]} - ${price:,.0f} ⭐"
                else:
                    expander_title = f"#{i}: {address[:50]} - ${price:,.0f}"
                
                with st.expander(expander_title):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("Price", f"${price:,.0f}")
                    col2.metric("Price/sqft", f"${ppsf:.2f}" if ppsf > 0 else "N/A")
                    col3.metric("Sqft", f"{sqft:,.0f}" if sqft > 0 else "N/A")
                    col4.metric("Beds/Baths", f"{int(beds) if beds else 0}/{int(baths) if baths else 0}")
                    col5.metric("Match", f"{similarity:.2%}" if similarity else "N/A")
                    
                    status_emoji = "✅ Sold" if status == "sold" else "🏷️ For Sale"
                    st.write(f"**Status:** {status_emoji}")
                    
                    # Display Zillow link
                    if zillow_url:
                        st.markdown(f"🔗 **[View on Zillow]({zillow_url})**", unsafe_allow_html=True)
        else:
            st.warning("⚠️ No comparable properties found")
        
        st.markdown("---")
        
        # Export Options
        st.markdown("## Export Report")
        
        col1, col2 = st.columns(2)
        with col1:
            # Export the full valuation report as JSON
            report_json = json.dumps(valuation_report, indent=2)
            st.download_button(
                label="Download Valuation Report (JSON)",
                data=report_json,
                file_name=f"valuation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # Export comparables as CSV
            if all_comparables:
                comp_data = []
                for comp in all_comparables:
                    price = comp.get('price', 0)
                    sqft = comp.get('living_area_sqft', 0)
                    ppsf = comp.get('price_per_sqft', 0)
                    similarity = comp.get('similarity_score', 0)
                    
                    comp_data.append({
                        "Address": comp.get('address', 'N/A'),
                        "Price": f"${price:,.0f}" if price else "N/A",
                        "Price/sqft": f"${ppsf:.2f}" if ppsf > 0 else "N/A",
                        "Sqft": f"{sqft:,.0f}" if sqft > 0 else "N/A",
                        "Beds": int(comp.get('bedrooms', 0)) if comp.get('bedrooms') else 0,
                        "Baths": comp.get('bathrooms', 0),
                        "Similarity": f"{similarity:.2%}" if similarity else "N/A",
                        "Status": comp.get('home_status', 'Unknown')
                    })
                
                import pandas as pd
                df = pd.DataFrame(comp_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Comparables (CSV)",
                    data=csv,
                    file_name=f"comparables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        st.markdown("---")
        st.success("Valuation Complete! Download your reports above.")
    
    except Exception as e:
        st.error(f"❌ Error during valuation: {str(e)}")
        st.write("Please check your input and try again.")
        import traceback
        st.write(traceback.format_exc())




