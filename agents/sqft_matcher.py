"""
Square Footage Matcher Utility
Matches target property sqft to fixed Zillow sqft ranges
"""

from typing import Dict, Tuple, Optional


class SqftMatcher:
    """
    Maps square footage to Zillow's fixed ranges
    Fixed ranges: 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 7000
    """
    
    # Fixed sqft ranges available on Zillow
    FIXED_SQFT_RANGES = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 7000]
    
    @classmethod
    def find_closest_range(cls, target_sqft: int) -> Tuple[Optional[int], Optional[int]]:
        """
        Find the closest sqft range for a given property size
        
        Returns min_sqft and max_sqft to use in Zillow filters
        
        Example:
            target_sqft = 2,300
            closest = 2,500
            returns (2,000, 3,000) for the range around 2,500
            
        Args:
            target_sqft: Target property square footage
        
        Returns:
            Tuple of (min_sqft, max_sqft) or (None, None) if can't determine
        """
        
        if not target_sqft or target_sqft <= 0:
            return None, None
        
        # Find closest value in fixed ranges
        closest = min(cls.FIXED_SQFT_RANGES, key=lambda x: abs(x - target_sqft))
        
        closest_idx = cls.FIXED_SQFT_RANGES.index(closest)
        
        # Build range: one below and one above the closest
        # Example: if closest=2500 (idx=4), range = [2000, 3000]
        
        min_sqft = None
        max_sqft = None
        
        # Set min_sqft to the value before closest
        if closest_idx > 0:
            min_sqft = cls.FIXED_SQFT_RANGES[closest_idx - 1]
        # If closest is first value (500), don't set min (let Zillow default)
        
        # Set max_sqft to the value after closest
        if closest_idx < len(cls.FIXED_SQFT_RANGES) - 1:
            max_sqft = cls.FIXED_SQFT_RANGES[closest_idx + 1]
        # If closest is last value (7000), don't set max (let Zillow default)
        
        return min_sqft, max_sqft
    
    @classmethod
    def get_sqft_filter_dict(cls, target_sqft: int) -> Dict:
        """
        Get filter state dict for sqft to add to search_state["filterState"]
        
        Args:
            target_sqft: Target property square footage
        
        Returns:
            Dict with min/max sqft or empty dict if no filter can be applied
        """
        
        min_sqft, max_sqft = cls.find_closest_range(target_sqft)
        
        if not min_sqft and not max_sqft:
            return {}
        
        filter_dict = {}
        if min_sqft:
            filter_dict["min"] = min_sqft
        if max_sqft:
            filter_dict["max"] = max_sqft
        
        return filter_dict
    
    @classmethod
    def log_matching(cls, target_sqft: int) -> str:
        """Get human-readable log message for sqft matching"""
        min_sqft, max_sqft = cls.find_closest_range(target_sqft)
        
        if not min_sqft and not max_sqft:
            return f"No sqft filter applied (property size {target_sqft} sqft is outside range)"
        
        closest = min(cls.FIXED_SQFT_RANGES, key=lambda x: abs(x - target_sqft))
        
        parts = []
        if min_sqft:
            parts.append(f"min: {min_sqft} sqft")
        if max_sqft:
            parts.append(f"max: {max_sqft} sqft")
        
        range_str = " - ".join(parts) if parts else "no range"
        
        return f"Target {target_sqft} sqft → Closest: {closest} sqft → Filter range: {range_str}"
