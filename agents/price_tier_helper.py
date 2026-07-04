"""
Price Tier Helper for Zillow Filtering
Generates dropdown options for min/max price selection
"""

from typing import List, Tuple


class PriceTierHelper:
    """
    Generates price tiers for Streamlit dropdowns
    
    Tiers:
    - $0 to $1M: Every $50k
    - $1M to $5M: Every $250k
    - $5M to $18M: Every $1M
    """
    
    @staticmethod
    def generate_price_tiers() -> List[int]:
        """
        Generate all price tier options
        
        Returns:
            List of prices in cents (for precision)
        """
        tiers = []
        
        # Tier 1: $0 to $1M in $50k increments
        for price in range(0, 1_000_001, 50_000):
            tiers.append(price)
        
        # Tier 2: $1M to $5M in $250k increments
        for price in range(1_250_000, 5_000_001, 250_000):
            tiers.append(price)
        
        # Tier 3: $5M to $18M in $1M increments
        for price in range(6_000_000, 18_000_001, 1_000_000):
            tiers.append(price)
        
        # Remove duplicates and sort
        tiers = sorted(list(set(tiers)))
        
        return tiers
    
    @staticmethod
    def format_price(price: int) -> str:
        """
        Format price for display
        
        Args:
            price: Price in dollars
        
        Returns:
            Formatted price string (e.g., "$1,250,000")
        """
        if price == 0:
            return "$0"
        elif price < 1_000_000:
            return f"${price:,}"
        elif price < 1_000_000_000:
            # Format as millions with decimals if needed
            millions = price / 1_000_000
            if millions == int(millions):
                return f"${int(millions)}M"
            else:
                return f"${millions:.2f}M"
        else:
            return f"${price:,}"
    
    @staticmethod
    def get_dropdown_options() -> dict:
        """
        Get formatted dropdown options
        
        Returns:
            Dict mapping display text to price value
        """
        tiers = PriceTierHelper.generate_price_tiers()
        options = {}
        
        for price in tiers:
            display = PriceTierHelper.format_price(price)
            options[display] = price
        
        return options
    
    @staticmethod
    def get_price_list() -> List[str]:
        """
        Get list of formatted prices for Streamlit selectbox
        
        Returns:
            List of formatted price strings
        """
        options = PriceTierHelper.get_dropdown_options()
        return list(options.keys())
    
    @staticmethod
    def get_price_value(display_text: str) -> int:
        """
        Get price value from display text
        
        Args:
            display_text: Formatted price (e.g., "$1.25M")
        
        Returns:
            Price in dollars
        """
        options = PriceTierHelper.get_dropdown_options()
        return options.get(display_text, 0)
