"""
Property Card Display Component for Streamlit
Displays properties in beautiful card format with images and details
"""

import streamlit as st
from typing import List, Dict, Any
import base64
from io import BytesIO


class PropertyCardDisplay:
    """Handles display of property cards in Streamlit"""
    
    @staticmethod
    def display_property_cards(properties: List[Dict[str, Any]], max_cols: int = 2) -> List[Dict[str, Any]]:
        """
        Display properties as cards in a grid layout
        Allows user to select properties
        
        Args:
            properties: List of property dictionaries from scraper
            max_cols: Number of columns in grid
        
        Returns:
            List of selected property objects
        """
        
        if not properties:
            st.warning("⚠️ No properties found to display")
            return []
        
        st.markdown("---")
        st.markdown(f"## 🏠 Available Properties ({len(properties)} found)")
        
        # Create selection checkboxes in session state if not exists
        if 'property_selections' not in st.session_state:
            st.session_state.property_selections = {}
        
        # Create columns for grid layout
        cols = st.columns(max_cols)
        
        for idx, prop in enumerate(properties):
            col = cols[idx % max_cols]
            
            with col:
                PropertyCardDisplay._render_card(prop, idx)
        
        st.markdown("---")
        
        # Get selected properties
        selected = PropertyCardDisplay._get_selected_properties(properties)
        
        # Display selection summary
        if selected:
            st.success(f"✅ {len(selected)} properties selected")
            with st.expander("📋 View Selected Properties"):
                for prop in selected:
                    st.write(f"• **{prop.get('address', 'Unknown')}** - ${prop.get('price', 'N/A'):,}")
        else:
            st.info("👆 Select properties above to continue")
        
        return selected
    
    @staticmethod
    def _render_card(property_data: Dict[str, Any], index: int):
        """
        Render a single property card
        
        Args:
            property_data: Property dictionary
            index: Index for unique key
        """
        
        address = property_data.get('address', 'Unknown Address')
        price = property_data.get('price', 0)
        beds = property_data.get('bedrooms', 'N/A')
        baths = property_data.get('bathrooms', 'N/A')
        sqft = property_data.get('living_area_sqft', 'N/A')
        image_url = property_data.get('image_url', '')
        status = property_data.get('home_status', 'unknown').upper()
        url = property_data.get('url', '')
        
        # Create unique key for checkbox (using index only to avoid special characters in address)
        checkbox_key = f"property_select_{index}"
        
        # Card container with CSS styling
        st.markdown("""
        <style>
        .property-card {
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 12px;
            margin: 8px 0;
            background: #f8f9fa;
            transition: all 0.3s ease;
        }
        
        .property-card:hover {
            border-color: #1f77b4;
            box-shadow: 0 4px 12px rgba(31, 119, 180, 0.15);
        }
        
        .property-price {
            font-size: 1.3rem;
            font-weight: 700;
            color: #1a1a1a;
            margin: 8px 0;
        }
        
        .property-address {
            font-size: 0.95rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }
        
        .property-details {
            display: flex;
            justify-content: space-around;
            font-size: 0.85rem;
            margin: 8px 0;
            padding: 8px 0;
            border-top: 1px solid #ddd;
            border-bottom: 1px solid #ddd;
        }
        
        .property-detail-item {
            text-align: center;
        }
        
        .property-detail-value {
            font-weight: 700;
            color: #1f77b4;
        }
        
        .property-status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 4px 0;
        }
        
        .property-status.for-sale {
            background-color: #e3f2fd;
            color: #1976d2;
        }
        
        .property-status.sold {
            background-color: #f3e5f5;
            color: #7b1fa2;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Render card
        with st.container(border=True):
            # Display image if available
            if image_url:
                try:
                    st.image(image_url, use_column_width=True, caption="Property Image")
                except:
                    st.info("📷 Image not available")
            else:
                st.info("📷 No image available")
            
            # Address
            st.markdown(f"**📍 {address}**", help=address)
            
            # Price - BIG AND PROMINENT
            if price and price != 0:
                st.markdown(f"## 💰 ${price:,}")
            
            # Details row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Beds", value=beds, label_visibility="collapsed")
            with col2:
                st.metric(label="Baths", value=baths, label_visibility="collapsed")
            with col3:
                st.metric(label="Sqft", value=f"{sqft:,}" if sqft != 'N/A' else 'N/A', label_visibility="collapsed")
            
            # Status badge
            status_color = "for-sale" if status == "FOR SALE" else "sold"
            st.markdown(
                f"<span class='property-status {status_color}'>{status}</span>",
                unsafe_allow_html=True
            )
            
            # Checkbox for selection
            is_selected = st.checkbox(
                "✅ Select this property",
                key=checkbox_key,
                value=st.session_state.property_selections.get(checkbox_key, False)
            )
            
            # Update session state
            st.session_state.property_selections[checkbox_key] = is_selected
            
            # View on Zillow button
            if url:
                st.markdown(
                    f"<a href='{url}' target='_blank' style='display: inline-block; background-color: #1f77b4; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 0.85rem;'>🔗 View on Zillow</a>",
                    unsafe_allow_html=True
                )
            
            # Additional details in expander
            with st.expander("📊 More Details"):
                # Price per sqft
                if sqft and sqft != 'N/A' and price and price != 0:
                    ppsf = price / sqft
                    st.metric("Price/sqft", f"${ppsf:.2f}")
                
                # Home type
                home_type = property_data.get('home_type', 'N/A')
                st.write(f"**Type:** {home_type}")
                
                # Year built
                year_built = property_data.get('year_built', 'N/A')
                st.write(f"**Year Built:** {year_built}")
                
                # Days on market
                days_on_market = property_data.get('days_on_market', 'N/A')
                st.write(f"**Days on Market:** {days_on_market}")
    
    @staticmethod
    def _get_selected_properties(properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get list of selected properties based on checkboxes
        
        Args:
            properties: List of all properties
        
        Returns:
            List of selected properties with their data
        """
        selected = []
        
        for idx, prop in enumerate(properties):
            address = prop.get('address', 'Unknown Address')
            checkbox_key = f"property_select_{idx}"
            
            # Check if this property was selected
            if st.session_state.property_selections.get(checkbox_key, False):
                selected.append(prop)
        
        return selected


def display_properties_for_selection(properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to display properties and get selections
    
    Args:
        properties: List of properties from scraper
    
    Returns:
        List of selected properties
    """
    return PropertyCardDisplay.display_property_cards(properties)
