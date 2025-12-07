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
    
    /* Property card styling */
    .property-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .property-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-left-color: #00cc00;
    }
    
    .property-card.selected {
        border-left-color: #00cc00;
        background-color: #e5ffe5;
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

# Initialize session state
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = None
if 'workflow_stage' not in st.session_state:
    st.session_state.workflow_stage = 'input'  # 'input', 'scraping', 'selecting', 'valuing', 'complete', 'email_creation'
if 'selected_property_indices' not in st.session_state:
    st.session_state.selected_property_indices = set()
if 'available_properties' not in st.session_state:
    st.session_state.available_properties = []
if 'property_details' not in st.session_state:
    st.session_state.property_details = {}
if 'filters' not in st.session_state:
    st.session_state.filters = {}
if 'graph_instance' not in st.session_state:
    st.session_state.graph_instance = None
if 'email_data' not in st.session_state:
    st.session_state.email_data = {}
if 'email_recipient_name' not in st.session_state:
    st.session_state.email_recipient_name = ''
if 'email_feedback_history' not in st.session_state:
    st.session_state.email_feedback_history = []
if 'email_iterations' not in st.session_state:
    st.session_state.email_iterations = 0

# Import price helper for filtering
from agents.price_tier_helper import PriceTierHelper

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
    
    # Price-based filtering section
    st.markdown("---")
    st.subheader("💰 Price Filtering")
    st.markdown("Filter comparable properties by price range:")
    
    # Get price tier options
    price_options = PriceTierHelper.get_price_list()
    
    # Price range selection
    col1_price, col2_price = st.columns(2)
    with col1_price:
        min_price_display = st.selectbox(
            "Min Price",
            options=["No minimum"] + price_options,
            index=0,
            help="Minimum price for comparable properties"
        )
    
    with col2_price:
        max_price_display = st.selectbox(
            "Max Price", 
            options=["No maximum"] + price_options,
            index=0,
            help="Maximum price for comparable properties"
        )
    
    # Convert display text to actual price values
    min_price = None if min_price_display == "No minimum" else PriceTierHelper.get_price_value(min_price_display)
    max_price = None if max_price_display == "No maximum" else PriceTierHelper.get_price_value(max_price_display)
    
    # Show selected range
    if min_price or max_price:
        range_text = ""
        if min_price and max_price:
            range_text = f"${min_price:,} - ${max_price:,}"
        elif min_price:
            range_text = f"${min_price:,}+"
        elif max_price:
            range_text = f"Up to ${max_price:,}"
        
        st.info(f"🎯 Price Filter: {range_text}")
    else:
        st.info("🎯 Price Filter: All prices")
    
    st.markdown("---")
    run_valuation = st.button("🚀 Run Valuation", width='stretch', type="primary")
    
    # Reset button
    if st.button("🔄 Reset", width='stretch'):
        st.session_state.workflow_state = None
        st.session_state.workflow_stage = 'input'
        st.session_state.selected_property_indices = set()
        st.session_state.available_properties = []
        st.session_state.property_details = {}
        st.session_state.filters = {}
        st.session_state.graph_instance = None
        st.rerun()

# Main page title
st.markdown("# Do Your Own CMA")

# Handle "Run Valuation" button click
if run_valuation and st.session_state.workflow_stage == 'input':
    # Store property details and filters in session state
    st.session_state.property_details = {
        "address": address,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "sqft": sqft,
        "asking_price": asking_price,
        "property_type": property_type,
        "year_built": year_built
    }
    
    st.session_state.filters = {
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "property_type": property_type.lower(),
        "min_price": min_price,
        "max_price": max_price,
        "min_sqft": None,
        "max_sqft": None,
        "year_built": year_built
    }
    
    st.session_state.workflow_stage = 'scraping'
    st.rerun()

# STAGE 1: Initial scraping (filter_capture → query_analysis → zip_discovery → scraping)
if st.session_state.workflow_stage == 'scraping':
    property_details = st.session_state.property_details
    filters = st.session_state.filters
    
    # Show initial property info
    with st.container():
        st.subheader("Property Information")
        
        # Display property image if available
        if property_details.get('image_url'):
            try:
                st.image(
                    property_details['image_url'], 
                    caption="Subject Property",
                    width=400
                )
            except Exception as e:
                st.write("📷 *Image not available*")
        else:
            st.write("📷 *No image available*")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Address", property_details['address'].split(",")[0])
        col2.metric("Bedrooms", f"{property_details['bedrooms']} bed | {property_details['bathrooms']} bath")
        col3.metric("Size", f"{property_details['sqft']:,} sqft")
        col4.metric("Asking Price", f"${property_details['asking_price']:,}")
    
    st.markdown("---")
    st.subheader("Valuation Progress")
    
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Node configuration
    nodes_list = ["filter_capture", "query_analysis", "zip_discovery", "scraping"]
    node_config = {
        "filter_capture": {"emoji": "🔧", "name": "Filter Setup"},
        "query_analysis": {"emoji": "🔍", "name": "Query Analysis"},
        "zip_discovery": {"emoji": "📍", "name": "ZIP Discovery"},
        "scraping": {"emoji": "🕷️", "name": "Scraping Zillow"}
    }
    
    try:
        # Initialize graph
        graph = RealEstateValuationGraph()
        st.session_state.graph_instance = graph
        
        user_query = f"Value my property at {property_details['address']}"
        
        # Initial state - only run up to scraping
        initial_state = {
            "user_query": user_query,
            "target_property": property_details,
            "filters": filters,
            "selected_properties": [],
            "query_analysis": {},
            "zip_discovery": {},
            "scraped_data": {},
            "preprocessed_data": {},
            "valuation_report": {},
            "email_data": {},
            "email_reflection_result": {},
            "workflow_start_time": datetime.now().isoformat(),
            "workflow_end_time": "",
            "total_execution_time_seconds": 0.0,
            "errors": [],
            "warnings": []
        }
        
        # Run nodes sequentially up to scraping
        current_state = initial_state
        
        for node_name in nodes_list:
            with status_placeholder.container():
                nodes_display = " → ".join([
                    f"{'✓' if nodes_list.index(n) < nodes_list.index(node_name) else '●' if n == node_name else '○'} {node_config[n]['name']}"
                    for n in nodes_list
                ])
                st.write(nodes_display)
                st.info(f"Processing: **{node_config[node_name]['name']}**")
            
            # Execute the node
            if node_name == "filter_capture":
                current_state = graph._node_filter_capture(current_state)
            elif node_name == "query_analysis":
                current_state = graph._node_query_analysis(current_state)
            elif node_name == "zip_discovery":
                current_state = graph._node_zip_discovery(current_state)
            elif node_name == "scraping":
                current_state = graph._node_scraping(current_state)
        
        # Mark all nodes as complete
        with status_placeholder.container():
            nodes_display = " → ".join([
                f"✓ {node_config[n]['name']}" for n in nodes_list
            ])
            st.write(nodes_display)
            st.success("✅ Scraping complete!")
        
        # Store workflow state and move to selection stage
        st.session_state.workflow_state = current_state
        st.session_state.available_properties = current_state.get('scraped_data', {}).get('for_sale_homes', [])
        st.session_state.workflow_stage = 'selecting'
        
        time.sleep(1)  # Brief pause to show completion
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during scraping: {str(e)}")
        with st.expander("Error Details"):
            import traceback
            st.code(traceback.format_exc())
        
        if st.button("Try Again"):
            st.session_state.workflow_stage = 'input'
            st.rerun()

# STAGE 2: Property selection
elif st.session_state.workflow_stage == 'selecting':
    property_details = st.session_state.property_details
    available_properties = st.session_state.available_properties
    
    # Show property info
    with st.container():
        st.subheader("Property Information")
        
        # Display property image if available
        if property_details.get('image_url'):
            try:
                st.image(
                    property_details['image_url'], 
                    caption="Subject Property",
                    width=400
                )
            except Exception as e:
                st.write("📷 *Image not available*")
        else:
            st.write("📷 *No image available*")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Address", property_details['address'].split(",")[0])
        col2.metric("Bedrooms", f"{property_details['bedrooms']} bed | {property_details['bathrooms']} bath")
        col3.metric("Size", f"{property_details['sqft']:,} sqft")
        col4.metric("Asking Price", f"${property_details['asking_price']:,}")
    
    st.markdown("---")
    
    if not available_properties:
        st.warning("⚠️ No properties found from scraping. Please try different search criteria.")
        if st.button("Start Over"):
            st.session_state.workflow_stage = 'input'
            st.rerun()
    else:
        st.markdown("## 📋 Select Comparable Properties")
        st.write(f"Found **{len(available_properties)}** properties. Select the ones you want to include in the valuation analysis:")
        
        # Select all / Deselect all buttons
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("✅ Select All", width='stretch'):
                st.session_state.selected_property_indices = set(range(len(available_properties)))
                st.rerun()
        with col2:
            if st.button("❌ Clear All", width='stretch'):
                st.session_state.selected_property_indices = set()
                st.rerun()
        
        st.markdown("---")
        
        # Display property cards with selection
        for idx, prop in enumerate(available_properties):
            is_selected = idx in st.session_state.selected_property_indices
            
            card_class = "property-card selected" if is_selected else "property-card"
            
            col1, col2 = st.columns([5, 1])
            
            with col1:
                with st.container():
                    st.markdown(f"### Property #{idx + 1}: {prop.get('address', 'Unknown')[:60]}")
                    
                    # Display property image if available
                    if prop.get('image_url'):
                        try:
                            st.image(
                                prop['image_url'], 
                                caption=f"Property #{idx + 1}",
                                width=300
                            )
                        except Exception as e:
                            st.write("📷 *Image not available*")
                    else:
                        st.write("📷 *No image available*")
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    price = prop.get('price') or 0
                    bedrooms = prop.get('bedrooms') or 0
                    bathrooms = prop.get('bathrooms') or 0
                    living_area = prop.get('living_area_sqft') or 0
                    price_per_sqft = prop.get('price_per_sqft') or 0
                    
                    col_a.metric("Price", f"${price:,}" if price else "N/A")
                    col_b.metric("Beds/Baths", f"{int(bedrooms)}/{int(bathrooms)}")
                    col_c.metric("Sqft", f"{living_area:,}" if living_area else "N/A")
                    col_d.metric("Price/sqft", f"${price_per_sqft:.2f}" if price_per_sqft else "N/A")
                    
                    # Additional details
                    details_col1, details_col2 = st.columns(2)
                    with details_col1:
                        st.write(f"**Type:** {prop.get('home_type', 'N/A')}")
                        st.write(f"**Year Built:** {prop.get('year_built', 'N/A')}")
                    with details_col2:
                        status = prop.get('home_status', 'N/A')
                        st.write(f"**Status:** {status.title() if status and status != 'N/A' else 'N/A'}")
                        if prop.get('url'):
                            st.markdown(f"🔗 [View on Zillow]({prop['url']})")
            
            with col2:
                # Checkbox for selection
                if st.checkbox(
                    "Include" if not is_selected else "✓ Included",
                    value=is_selected,
                    key=f"select_{idx}",
                    help="Include this property in valuation analysis"
                ):
                    st.session_state.selected_property_indices.add(idx)
                else:
                    st.session_state.selected_property_indices.discard(idx)
            
            st.markdown("---")
        
        # Continue button
        st.markdown("### Ready to Continue?")
        selected_count = len(st.session_state.selected_property_indices)
        
        if selected_count == 0:
            st.warning("⚠️ Please select at least one property to continue")
        else:
            st.info(f"✅ **{selected_count}** properties selected")
            
            if st.button("🚀 Continue to Valuation", type="primary", width='stretch'):
                st.session_state.workflow_stage = 'valuing'
                st.rerun()

# STAGE 3: Valuation (preprocessing → valuation → email_generation → email_reflection)
elif st.session_state.workflow_stage == 'valuing':
    property_details = st.session_state.property_details
    
    # Show property info
    with st.container():
        st.subheader("Property Information")
        
        # Display property image if available
        if property_details.get('image_url'):
            try:
                st.image(
                    property_details['image_url'], 
                    caption="Subject Property",
                    width=400
                )
            except Exception as e:
                st.write("📷 *Image not available*")
        else:
            st.write("📷 *No image available*")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Address", property_details['address'].split(",")[0])
        col2.metric("Bedrooms", f"{property_details['bedrooms']} bed | {property_details['bathrooms']} bath")
        col3.metric("Size", f"{property_details['sqft']:,} sqft")
        col4.metric("Asking Price", f"${property_details['asking_price']:,}")
    
    st.markdown("---")
    st.subheader("Valuation Progress")
    
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Node configuration for valuation stage
    nodes_list = ["preprocessing", "valuation"]
    node_config = {
        "preprocessing": {"emoji": "🔄", "name": "Processing Data"},
        "valuation": {"emoji": "💰", "name": "Final Valuation"}
    }
    
    try:
        # Get selected properties
        selected_indices = st.session_state.selected_property_indices
        available_properties = st.session_state.available_properties
        selected_properties = [available_properties[i] for i in selected_indices]
        
        st.info(f"🔍 Analyzing {len(selected_properties)} selected properties...")
        
        # Get current state and graph
        current_state = st.session_state.workflow_state
        graph = st.session_state.graph_instance
        
        # Update state with selected properties
        current_state['selected_properties'] = selected_properties
        
        # Update scraped_data to only include selected properties
        current_state['scraped_data']['for_sale_homes'] = selected_properties
        
        # Run preprocessing and valuation nodes
        for node_name in nodes_list:
            with status_placeholder.container():
                nodes_display = " → ".join([
                    f"{'✓' if nodes_list.index(n) < nodes_list.index(node_name) else '●' if n == node_name else '○'} {node_config[n]['name']}"
                    for n in nodes_list
                ])
                st.write(nodes_display)
                st.info(f"Processing: **{node_config[node_name]['name']}**")
            
            # Execute the node
            if node_name == "preprocessing":
                current_state = graph._node_preprocessing(current_state)
            elif node_name == "valuation":
                current_state = graph._node_valuation(current_state)
        
        # Mark all nodes as complete
        with status_placeholder.container():
            nodes_display = " → ".join([
                f"✓ {node_config[n]['name']}" for n in nodes_list
            ])
            st.write(nodes_display)
            st.success("✅ Valuation complete!")
        
        # Store final state
        st.session_state.workflow_state = current_state
        st.session_state.workflow_stage = 'complete'
        
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during valuation: {str(e)}")
        with st.expander("Error Details"):
            import traceback
            st.code(traceback.format_exc())
        
        if st.button("Back to Selection"):
            st.session_state.workflow_stage = 'selecting'
            st.rerun()

# STAGE 4: Display results
elif st.session_state.workflow_stage == 'complete':
    result = st.session_state.workflow_state
    property_details = st.session_state.property_details
    
    # Show property info
    with st.container():
        st.subheader("Property Information")
        
        # Display property image if available
        if property_details.get('image_url'):
            try:
                st.image(
                    property_details['image_url'], 
                    caption="Subject Property",
                    width=400
                )
            except Exception as e:
                st.write("📷 *Image not available*")
        else:
            st.write("📷 *No image available*")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Address", property_details['address'].split(",")[0])
        col2.metric("Bedrooms", f"{property_details['bedrooms']} bed | {property_details['bathrooms']} bath")
        col3.metric("Size", f"{property_details['sqft']:,} sqft")
        col4.metric("Asking Price", f"${property_details['asking_price']:,}")
    
    st.markdown("---")
    
    # Extract results
    valuation_report = result.get('valuation_report', {})
    preprocessed_data = result.get('preprocessed_data', {})
    
    # RESULTS SECTION
    st.markdown("## 💰 VALUATION COMPLETE")
    
    # Extract valuation data
    analysis_summary = valuation_report.get('analysis_summary', {})
    why_this_price = valuation_report.get('why_this_price', '')
    
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
    except ValueError:
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
    st.markdown("## 📊 VALUATION VERDICT")
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
            <div style="display: flex; align-items: center; justify-content: center; font-size: 5rem;">
                {verdict_icon}
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Executive Summary
    st.markdown("## 📝 Why This Valuation?")
    if why_this_price:
        st.text(why_this_price)
    else:
        st.info("No detailed summary available")
    
    st.markdown("---")
    
    # Confidence & Summary Section
    st.markdown("## 🎯 Valuation Confidence & Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Confidence Level", confidence_level.title())
    col2.metric("Confidence Score", f"{confidence_score:.2f}")
    col3.metric("Comparables Used", comps_used)
    
    st.markdown("---")
    
    # Price Estimate
    st.markdown("## 💵 Price Estimate")
    col1, col2 = st.columns(2)
    col1.metric("Estimated Value", f"${estimated_mid:,.0f}")
    col2.metric("Asking Price", f"${asking_price_num:,.0f}")
    
    st.markdown("---")
    
    # Comparable Analysis
    st.markdown("## 🏘️ Comparable Properties Used")
    
    sold_homes = preprocessed_data.get('filtered_sold_homes', [])
    for_sale_homes = preprocessed_data.get('filtered_for_sale_homes', [])
    
    all_comparables = sold_homes if sold_homes else for_sale_homes
    
    if all_comparables:
        st.markdown(f"**Analyzed {len(all_comparables)} Comparable Properties**")
        
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
                expander_title = f"#{i}: {address[:50]} - ${price:,.0f} ⭐ High Match"
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
                
                if zillow_url:
                    st.markdown(f"🔗 **[View on Zillow]({zillow_url})**")
    else:
        st.warning("⚠️ No comparable properties found")
    
    st.markdown("---")
    
    # Action buttons
    st.markdown("## 🎬 Next Steps")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("� Create Email", width='stretch', type="secondary"):
            st.session_state.workflow_stage = 'email_creation'
            st.rerun()
    
    with col2:
        if st.button("�🔄 Analyze New Property", width='stretch', type="primary"):
            # Reset everything
            st.session_state.workflow_state = None
            st.session_state.workflow_stage = 'input'
            st.session_state.selected_property_indices = set()
            st.session_state.available_properties = []
            st.session_state.property_details = {}
            st.session_state.filters = {}
            st.session_state.graph_instance = None
            st.rerun()
    
    with col3:
        if st.button("◀️ Back to Property Selection", width='stretch'):
            st.session_state.workflow_stage = 'selecting'
            st.rerun()
    
    st.markdown("---")
    st.success("✅ Valuation Complete! Use buttons above to analyze another property or review property selections.")

# STAGE 5: Email Creation
elif st.session_state.workflow_stage == 'email_creation':
    result = st.session_state.workflow_state
    property_details = st.session_state.property_details
    
    # Show property info
    with st.container():
        st.subheader("Property Information")
        
        # Display property image if available
        if property_details.get('image_url'):
            try:
                st.image(
                    property_details['image_url'], 
                    caption="Subject Property",
                    width=400,
                    
                )
            except Exception as e:
                st.write("📷 *Image not available*")
        else:
            st.write("📷 *No image available*")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Address", property_details['address'].split(",")[0])
        col2.metric("Bedrooms", f"{property_details['bedrooms']} bed | {property_details['bathrooms']} bath")
        col3.metric("Size", f"{property_details['sqft']:,} sqft")
        col4.metric("Asking Price", f"${property_details['asking_price']:,}")
    
    st.markdown("---")
    st.markdown("## 📧 Client Email Creation")
    
    # Email recipient input
    if not st.session_state.email_recipient_name:
        st.markdown("### Step 1: Enter Client Information")
        recipient_name = st.text_input(
            "Client Name",
            placeholder="e.g., John Smith",
            help="Enter the name of your client who will receive this email"
        )
        
        if recipient_name:
            st.session_state.email_recipient_name = recipient_name
            st.rerun()
    else:
        st.info(f"📨 Creating email for: **{st.session_state.email_recipient_name}**")
        
        # Generate initial email if not already generated
        if not st.session_state.email_data and st.session_state.email_iterations == 0:
            st.markdown("### Step 2: Generating Email...")
            
            with st.spinner("🤖 AI is crafting your professional email..."):
                try:
                    from agents.email_generator import EmailGeneratorAgent
                    
                    # Initialize email generator
                    email_generator = EmailGeneratorAgent()
                    
                    # Generate email using the current state
                    email_data = email_generator.generate_email(
                        st.session_state.workflow_state, 
                        st.session_state.email_recipient_name
                    )
                    
                    st.session_state.email_data = email_data
                    st.session_state.email_iterations = 1
                    
                    st.success("✅ Email generated successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error generating email: {str(e)}")
                    if st.button("Try Again"):
                        st.rerun()
        
        # Show email and feedback interface
        if st.session_state.email_data:
            st.markdown("### Step 3: Review & Refine Email")
            
            # Display current email iteration
            if st.session_state.email_iterations > 1:
                st.info(f"📝 Email iteration #{st.session_state.email_iterations}")
            
            # Email preview
            email_data = st.session_state.email_data
            
            # Email container with tabs
            tab1, tab2 = st.tabs(["📧 Email Preview", "📝 Edit Email"])
            
            with tab1:
                # Subject
                st.markdown("**Subject:**")
                st.code(email_data.get('subject', 'No subject'), language=None)
                
                st.markdown("**Email Body:**")
                email_body = email_data.get('body', 'No body content')
                
                # Enhanced email display with better formatting
                st.markdown("---")
                
                # Show property image if available
                if property_details.get('image_url'):
                    try:
                        col_img, col_text = st.columns([1, 2])
                        with col_img:
                            st.image(
                                property_details['image_url'],
                                caption="Property Image",
                                width=200
                            )
                        with col_text:
                            st.markdown("### 📧 Client Email Preview")
                            st.markdown(f"**To:** {st.session_state.email_recipient_name}")
                            st.markdown(f"**Subject:** {email_data.get('subject', 'No subject')}")
                    except Exception as e:
                        st.markdown("### 📧 Client Email Preview")
                        st.markdown(f"**To:** {st.session_state.email_recipient_name}")
                        st.markdown(f"**Subject:** {email_data.get('subject', 'No subject')}")
                else:
                    st.markdown("### 📧 Client Email Preview")
                    st.markdown(f"**To:** {st.session_state.email_recipient_name}")
                    st.markdown(f"**Subject:** {email_data.get('subject', 'No subject')}")
                
                st.markdown("---")
                st.markdown("**Email Content:**")
                st.markdown("---")

                import re

                # Add custom CSS for email styling
                st.markdown("""
                <style>
                .email-content {
                    background-color: #ffffff;
                    padding: 2rem;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                    line-height: 1.8;
                    color: #1a1a1a;
                    font-size: 1rem;
                }

                .email-content p {
                    margin-bottom: 1.5rem;
                }

                .email-content a {
                    color: #1f77b4;
                    text-decoration: none;
                    font-weight: 500;
                    border-bottom: 1px solid transparent;
                    transition: border-bottom 0.2s ease;
                }

                .email-content a:hover {
                    border-bottom: 1px solid #1f77b4;
                }

                .email-greeting {
                    font-style: italic;
                    color: #333;
                }

                .email-closing {
                    margin-top: 2rem;
                    font-style: italic;
                    color: #555;
                }
                </style>
                """, unsafe_allow_html=True)

                # Convert markdown links to HTML
                def format_email_html(text):
                    # Convert markdown links to HTML
                    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
                    text = re.sub(pattern, r'<a href="\2" target="_blank">\1</a>', text)
                    
                    # Split into paragraphs
                    paragraphs = text.split('\n')
                    
                    html_parts = ['<div class="email-content">']
                    
                    for i, para in enumerate(paragraphs):
                        para = para.strip()
                        if para:
                            if i == 0:
                                # First paragraph (greeting)
                                html_parts.append(f'<p class="email-greeting">{para}</p>')
                            elif 'Best regards' in para or 'Sincerely' in para:
                                # Closing
                                html_parts.append(f'<p class="email-closing">{para}</p>')
                            else:
                                # Regular paragraph
                                html_parts.append(f'<p>{para}</p>')
                    
                    html_parts.append('</div>')
                    return ''.join(html_parts)

                # Format and display
                formatted_html = format_email_html(email_body)
                st.markdown(formatted_html, unsafe_allow_html=True)
                
                if st.session_state.workflow_state:
                    selected_properties = st.session_state.workflow_state.get('selected_properties', [])
                    if selected_properties:
                        st.markdown("---")
                        st.markdown("### 🏘️ Referenced Comparable Properties")
                        
                        # Show properties in a grid
                        for i, prop in enumerate(selected_properties[:6]):  # Show max 6 properties
                            with st.expander(f"🏠 {prop.get('address', 'Unknown Address')[:50]}"):
                                col_prop_img, col_prop_details = st.columns([1, 2])
                                
                                with col_prop_img:
                                    if prop.get('image_url'):
                                        try:
                                            st.image(
                                                prop['image_url'],
                                                caption="Property",
                                                width=150
                                            )
                                        except:
                                            st.write("📷 *Image not available*")
                                    else:
                                        st.write("📷 *No image*")
                                
                                with col_prop_details:
                                    price = prop.get('price', 0)
                                    beds = prop.get('bedrooms', 'N/A')
                                    baths = prop.get('bathrooms', 'N/A')
                                    sqft = prop.get('living_area_sqft', 'N/A')
                                    ppsf = prop.get('price_per_sqft', 0)
                                    
                                    st.markdown(f"**Price:** ${price:,}" if price else "**Price:** N/A")
                                    st.markdown(f"**Beds/Baths:** {beds}/{baths}")
                                    st.markdown(f"**Square Feet:** {sqft:,}" if sqft != 'N/A' else "**Square Feet:** N/A")
                                    st.markdown(f"**Price/sqft:** ${ppsf:.2f}" if ppsf else "**Price/sqft:** N/A")
                                    
                                    if prop.get('url'):
                                        st.markdown(f"🔗 **[View on Zillow]({prop['url']})**")
            
            with tab2:
                st.markdown("### Manual Edits")
                st.info("💡 Make direct changes to the email content below")
                
                # Editable subject
                edited_subject = st.text_input(
                    "Subject Line:",
                    value=email_data.get('subject', ''),
                    key=f"subject_edit_{st.session_state.email_iterations}"
                )
                
                # Editable body
                edited_body = st.text_area(
                    "Email Body:",
                    value=email_data.get('body', ''),
                    height=400,
                    key=f"body_edit_{st.session_state.email_iterations}"
                )
                
                if st.button("💾 Save Manual Edits", width='stretch'):
                    st.session_state.email_data['subject'] = edited_subject
                    st.session_state.email_data['body'] = edited_body
                    st.success("✅ Manual edits saved!")
                    st.rerun()
            
            st.markdown("---")
            
            # Feedback interface
            st.markdown("### Step 4: Provide Feedback for AI Improvement")
            st.markdown("Tell the AI how to improve the email. Be specific about tone, content, or style changes.")
            
            feedback = st.text_area(
                "Your Feedback",
                placeholder="e.g., Make it more casual and friendly, add more details about the neighborhood, emphasize the good value, etc.",
                height=100,
                key=f"feedback_{st.session_state.email_iterations}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Regenerate with Feedback", width='stretch', type="primary", disabled=not feedback.strip()):
                    if feedback.strip():
                        # Add feedback to history
                        st.session_state.email_feedback_history.append({
                            'iteration': st.session_state.email_iterations,
                            'feedback': feedback.strip(),
                            'previous_email': st.session_state.email_data.copy()
                        })
                        
                        with st.spinner("🤖 AI is incorporating your feedback..."):
                            try:
                                from agents.email_generator import EmailGeneratorAgent
                                
                                email_generator = EmailGeneratorAgent()
                                
                                # Create enhanced state with feedback
                                enhanced_state = st.session_state.workflow_state.copy()
                                enhanced_state['user_feedback'] = feedback.strip()
                                enhanced_state['previous_email'] = st.session_state.email_data
                                enhanced_state['feedback_history'] = st.session_state.email_feedback_history
                                
                                # Generate improved email
                                improved_email = email_generator.generate_email(
                                    enhanced_state,
                                    st.session_state.email_recipient_name
                                )
                                
                                st.session_state.email_data = improved_email
                                st.session_state.email_iterations += 1
                                
                                st.success(f"✅ Email improved! (Iteration #{st.session_state.email_iterations})")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Error improving email: {str(e)}")
            
            with col2:
                if st.button("✅ Email is Ready", width='stretch', type="secondary"):
                    st.session_state.email_final = True
                    st.success("🎉 Email finalized! Scroll down for copy/download options.")
            
            if st.session_state.email_feedback_history:
                st.markdown("---")
                with st.expander(f"📋 Feedback History ({len(st.session_state.email_feedback_history)} iterations)"):
                    for i, feedback_item in enumerate(st.session_state.email_feedback_history, 1):
                        st.markdown(f"**Iteration {feedback_item['iteration']}:**")
                        st.text(feedback_item['feedback'])
                        if i < len(st.session_state.email_feedback_history):
                            st.markdown("---")
    
    if st.session_state.email_data and st.session_state.get('email_final', False):
        st.markdown("---")
        st.markdown("## 🎬 Final Email Actions")
        
        email_data = st.session_state.email_data
        full_email = f"Subject: {email_data.get('subject', '')}\n\n{email_data.get('body', '')}"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📥 Download Email",
                data=full_email,
                file_name=f"client_email_{st.session_state.email_recipient_name.replace(' ', '_').lower()}.txt",
                mime="text/plain",
                width='stretch'
            )
        
        with col2:
            if st.button("📋 Copy to Clipboard", width='stretch'):
                # Simple copy functionality
                st.code(full_email, language=None)
                st.info("👆 Email content above - select all and copy (Ctrl+C / Cmd+C)")
        
        with col3:
            if st.button("◀️ Back to Results", width='stretch'):
                # Reset email state and go back to complete
                st.session_state.email_data = {}
                st.session_state.email_recipient_name = ''
                st.session_state.email_feedback_history = []
                st.session_state.email_iterations = 0
                st.session_state.email_final = False
                st.session_state.workflow_stage = 'complete'
                st.rerun()
        
        st.markdown("---")
        
        # Navigation options
        st.markdown("### What's Next?")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Analyze New Property", width='stretch', type="primary"):
                # Reset everything for new analysis
                st.session_state.workflow_state = None
                st.session_state.workflow_stage = 'input'
                st.session_state.selected_property_indices = set()
                st.session_state.available_properties = []
                st.session_state.property_details = {}
                st.session_state.filters = {}
                st.session_state.graph_instance = None
                # Reset email state
                st.session_state.email_data = {}
                st.session_state.email_recipient_name = ''
                st.session_state.email_feedback_history = []
                st.session_state.email_iterations = 0
                st.session_state.email_final = False
                st.rerun()
        
        with col2:
            if st.button("📧 Create Another Email", width='stretch'):
                # Reset email state but keep valuation
                st.session_state.email_data = {}
                st.session_state.email_recipient_name = ''
                st.session_state.email_feedback_history = []
                st.session_state.email_iterations = 0
                st.session_state.email_final = False
                st.rerun()

# Show instructions if in input stage
if st.session_state.workflow_stage == 'input':
    st.markdown("""
    ## 👋 Welcome to CMA Analysis
    
    This tool helps you perform a **Comparative Market Analysis (CMA)** using AI-powered agents:
    
    ### How it works:
    1. **Enter property details** in the sidebar (address, beds, baths, etc.)
    2. **Click "Run Valuation"** to start the analysis
    3. **Review scraped properties** and select which ones to include
    4. **Get AI-powered valuation** with detailed comparable analysis
    
    ### Features:
    - 🔍 Intelligent ZIP code discovery
    - 🕷️ Real-time Zillow scraping
    - 🎯 Property type filtering
    - 📊 AI-powered valuation analysis
    - 🏘️ Detailed comparable breakdowns
    
    **Ready to start?** Fill in the property details on the left and click "Run Valuation"!
    """)