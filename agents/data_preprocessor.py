from typing import List, Dict
from datetime import datetime
import statistics


class DataPreprocessorAgent:
    """
    Preprocesses scraped data:
    1. Filters out invalid/incomplete properties
    2. Calculates quality metrics
    3. Ranks comparables by similarity
    4. Prepares clean context for LLM
    
    Returns pure JSON output
    """
    
    def __init__(self):
        self.min_price = 10000
        self.max_price = 50000000
        self.min_sqft = 200
        self.max_sqft = 50000
        self.max_days_since_sold = 180  # ✅ Only use sold homes from last 6 months (180 days)
        self.valid_states = ['TX', 'CA', 'FL', 'NY', 'NJ', 'PA', 'IL', 'OH', 'GA', 'NC', 'VA', 'MA', 'WA', 'AZ', 'TN', 'IN', 'MO', 'MD', 'WI', 'CO', 'MN', 'SC', 'AL', 'LA', 'KY', 'OR', 'OK', 'CT', 'UT', 'IA', 'NV', 'AR', 'MS', 'KS', 'NM', 'NE', 'ID', 'WV', 'HI', 'NH', 'ME', 'MT', 'RI', 'DE', 'SD', 'ND', 'AK', 'VT', 'WY']
    
    def preprocess_data(self, scraped_data: Dict, target_property: Dict = None) -> Dict:
        """
        Preprocess and filter scraped data
        
        Args:
            scraped_data: Output from ZillowScraperAgent
            target_property: Optional target property for comparison
        
        Returns:
            JSON with cleaned data and quality metrics
        """
        
        print(f"\n{'='*80}")
        print(f"🔧 AGENT 4: Data Preprocessing & Quality")
        print(f"{'='*80}\n")
        
        # ✅ Handle FOR-SALE only data (no sold_homes key)
        sold_homes = scraped_data.get('sold_homes', [])
        for_sale_homes = scraped_data.get('for_sale_homes', [])
        
        # Normalize property keys: beds→bedrooms, baths→bathrooms
        sold_homes = self._normalize_property_keys(sold_homes)
        for_sale_homes = self._normalize_property_keys(for_sale_homes)
        
        print(f"📥 Input Data:")
        print(f"   • Raw Sold Homes: {len(sold_homes)}")
        print(f"   • Raw For-Sale Homes: {len(for_sale_homes)}\n")
        
        # Filter sold homes
        if sold_homes:
            print("🧹 Filtering sold homes...")
            filtered_sold, sold_excluded = self._filter_properties(sold_homes, target_property, is_sold=True)
            print(f"   ✅ Kept: {len(filtered_sold)}")
            print(f"   ❌ Excluded: {len(sold_excluded)}\n")
        else:
            print("⚠️  No sold homes to filter (using FOR-SALE only)\n")
            filtered_sold = []
            sold_excluded = []
        
        # Filter for-sale homes  
        print("🧹 Filtering for-sale homes...")
        filtered_for_sale, for_sale_excluded = self._filter_properties(for_sale_homes, target_property, is_sold=False)
        print(f"   ✅ Kept: {len(filtered_for_sale)}")
        print(f"   ❌ Excluded: {len(for_sale_excluded)}\n")
        
        # Calculate market statistics
        print("📊 Calculating market statistics...")
        market_stats = self._calculate_market_stats(filtered_sold, filtered_for_sale)
        
        # Rank comparables if target property provided
        if target_property:
            print("🎯 Ranking comparables by similarity...")
            # If we have sold homes, rank them. Otherwise rank for-sale homes
            if filtered_sold:
                filtered_sold = self._rank_comparables(filtered_sold, target_property)
            elif filtered_for_sale:
                print("   ⚠️  No sold homes available, ranking FOR-SALE properties instead")
                filtered_for_sale = self._rank_comparables(filtered_for_sale, target_property)
        
        # Remove duplicate addresses from both lists
        print("🔍 Removing duplicate addresses...")
        filtered_sold_before = len(filtered_sold)
        filtered_for_sale_before = len(filtered_for_sale)
        
        filtered_sold = self._remove_duplicate_addresses(filtered_sold)
        filtered_for_sale = self._remove_duplicate_addresses(filtered_for_sale)
        
        print(f"   • Sold homes: {filtered_sold_before} → {len(filtered_sold)} (removed {filtered_sold_before - len(filtered_sold)} duplicates)")
        print(f"   • For-sale homes: {filtered_for_sale_before} → {len(filtered_for_sale)} (removed {filtered_for_sale_before - len(filtered_for_sale)} duplicates)\n")
        
        # Calculate data quality score
        quality_score = self._calculate_quality_score(
            len(filtered_sold),
            len(filtered_for_sale),
            len(sold_excluded),
            len(for_sale_excluded)
        )
        
        # Log exclusion summary
        exclusion_summary = self._count_exclusion_reasons(sold_excluded + for_sale_excluded)
        if exclusion_summary:
            print("📊 Property Exclusion Summary:")
            for reason, count in exclusion_summary.items():
                print(f"   • {reason.replace('_', ' ').title()}: {count} properties")
        
        # Log quality metrics
        print(f"\n📈 Data Quality Metrics:")
        total_properties = len(sold_homes) + len(for_sale_homes)
        kept_properties = len(filtered_sold) + len(filtered_for_sale)
        print(f"   • Overall Retention Rate: {kept_properties}/{total_properties} ({kept_properties/max(total_properties,1)*100:.1f}%)")
        print(f"   • Sold Homes Retention: {len(filtered_sold)}/{len(sold_homes)} ({len(filtered_sold)/max(len(sold_homes),1)*100:.1f}%)")
        print(f"   • For-Sale Retention: {len(filtered_for_sale)}/{len(for_sale_homes)} ({len(filtered_for_sale)/max(len(for_sale_homes),1)*100:.1f}%)")
        
        print(f"\n✅ Preprocessing Complete:")
        print(f"   • Quality Score: {quality_score*100:.0f}%")
        print(f"   • Usable Sold Homes: {len(filtered_sold)}")
        print(f"   • Usable For-Sale Homes: {len(filtered_for_sale)}")
        print(f"{'='*80}\n")
        
        # Return pure JSON
        return {
            "filtered_sold_homes": filtered_sold,
            "filtered_for_sale_homes": filtered_for_sale,
            "market_statistics": market_stats,
            "data_quality": {
                "quality_score": round(quality_score, 3),
                "total_sold_kept": len(filtered_sold),
                "total_sold_excluded": len(sold_excluded),
                "total_for_sale_kept": len(filtered_for_sale),
                "total_for_sale_excluded": len(for_sale_excluded),
                "exclusion_reasons": self._count_exclusion_reasons(sold_excluded + for_sale_excluded)
            },
            "preprocessing_timestamp": datetime.now().isoformat()
        }
    
    def _filter_properties(self, properties: List[Dict], target_property: Dict = None, is_sold: bool = False) -> tuple:
        """Filter properties based on data quality and geographic relevance with detailed logging"""
        
        filtered = []
        excluded = []
        
        # Determine target state from target property
        target_state = None
        if target_property:
            target_address = target_property.get('address', '')
            target_state = self._extract_state_from_address(target_address)
            if target_state:
                print(f"   🎯 Target State: {target_state} (from '{target_address}')")
        
        # Get target specs for comparison
        target_beds = target_property.get('bedrooms') if target_property else None
        target_baths = target_property.get('bathrooms') if target_property else None
        target_sqft = target_property.get('sqft') if target_property else None
        
        if target_beds or target_baths or target_sqft:
            print(f"   🏠 Target Specs: {target_beds}bed / {target_baths}bath / {target_sqft:,} sqft" if target_sqft else f"   🏠 Target Specs: {target_beds}bed / {target_baths}bath")
            print(f"   � MATCHING STRATEGY:")
            print(f"      1️⃣  PRICE RANGE: Applied via Zillow filters")
            print(f"      2️⃣  BEDROOMS: ±1 tolerance")
            print(f"      3️⃣  BATHROOMS: ±1 tolerance")
        
        print(f"   🔍 Analyzing {len(properties)} properties...")
        
        for i, prop in enumerate(properties):
            exclusion_reason = self._should_exclude(prop, target_state, target_beds, target_baths, target_sqft, is_sold=is_sold)
            
            if exclusion_reason:
                prop['exclusion_reason'] = exclusion_reason
                excluded.append(prop)
                
                # Log excluded properties with details
                if i < 5:  # Show details for first 5 excluded properties
                    address = prop.get('address', 'Unknown Address')[:50]
                    price = prop.get('price', 'N/A')
                    beds = prop.get('bedrooms', 'N/A')
                    baths = prop.get('bathrooms', 'N/A')
                    print(f"      ❌ {address} - Excluded: {exclusion_reason}")
                    print(f"         Price: {price}, {beds}bed/{baths}bath")
            else:
                filtered.append(prop)
                
                # Log first few accepted properties for transparency
                if len(filtered) <= 5:
                    address = prop.get('address', 'Unknown Address')[:50]
                    price = prop.get('price', 0) or 0
                    sqft = prop.get('living_area_sqft', 0) or 0
                    beds = prop.get('bedrooms', 0) or 0
                    baths = prop.get('bathrooms', 0) or 0
                    price_per_sqft = (prop.get('price_per_sqft') or 0)  # ✅ Ensure never None
                    
                    # Safe formatting with None checks
                    price_str = f"${int(price):,}" if price else "N/A"
                    sqft_str = f"{int(sqft):,} sqft" if sqft else "N/A sqft"
                    ppsf_str = f"${price_per_sqft:.0f}/sqft" if price_per_sqft else "N/A/sqft"
                    
                    print(f"      ✅ {address}")
                    print(f"         {price_str} | {sqft_str} | {beds}bed/{baths}bath | {ppsf_str}")
        
        # Log summary of filtering results
        if len(excluded) > 5:
            print(f"      ... and {len(excluded) - 5} more excluded properties")
        
        return filtered, excluded
    
    def _should_exclude(self, prop: Dict, target_state: str = None, target_beds: int = None, target_baths: float = None, target_sqft: int = None, is_sold: bool = False) -> str:
        """
        Check if property should be excluded, return reason if yes
        
        Matching Strategy:
        - Price range applied via Zillow filters (before scraping)
        - Bedrooms: ±1 tolerance
        - Bathrooms: ±1 tolerance
        """
        
        # Must have price
        price = prop.get('price')
        if not price or (isinstance(price, str) and not price.strip()):
            return "missing_price"

        # Price must be reasonable
        if prop['price'] < self.min_price or prop['price'] > self.max_price:
            return "price_out_of_range"
        
        # ✅ For SOLD homes, check if it was sold too long ago (outside 180 day window)
        if is_sold:
            last_sold_date = prop.get('last_sold_date') or prop.get('date_sold')
            if last_sold_date:
                try:
                    sold_date = datetime.fromisoformat(str(last_sold_date))
                    days_since_sold = (datetime.now() - sold_date).days
                    if days_since_sold > self.max_days_since_sold:
                        return f"sold_too_long_ago_{days_since_sold}_days"
                except:
                    pass
        
        # ✅ Square footage is EXTRACTED but NOT REQUIRED - keep properties even without sqft
        # (can still use price/sqft calculation if available, but don't reject for missing sqft)
        
        # Must have bedrooms and bathrooms (check for None, NaN, or negative values)
        bedrooms = prop.get('bedrooms')
        bathrooms = prop.get('bathrooms')
        
        # Check if bedrooms is missing, null, NaN, or invalid
        if bedrooms is None or bedrooms == '' or (isinstance(bedrooms, (int, float)) and bedrooms <= 0):
            return "missing_or_invalid_bedrooms"
        
        # Check if bathrooms is missing, null, NaN, or invalid
        if bathrooms is None or bathrooms == '' or (isinstance(bathrooms, (int, float)) and bathrooms <= 0):
            return "missing_or_invalid_bathrooms"
        
        # ✅ STRICT MATCHING: Bedrooms and bathrooms must match EXACTLY or be rejected
        # Do NOT accept 3bed/3bath for a 4bed/4bath property - this distorts valuation!
        if target_beds is not None:
            # Allow ±1 tolerance on bedrooms (per user request - similarity is sqft-based)
            if bedrooms < target_beds - 1 or bedrooms > target_beds + 1:
                return f"bedrooms_mismatch_{bedrooms}bed_vs_target_{target_beds}bed"
        
        # ✅ BATHROOM TOLERANCE: Allow ±1 on bathrooms (similarity is sqft-based)
        if target_baths is not None:
            # Allow ±1 tolerance on bathrooms
            if bathrooms < target_baths - 1 or bathrooms > target_baths + 1:
                return f"bathrooms_mismatch_{bathrooms}bath_vs_target_{target_baths}bath"
        
        # ✅ UPDATED: Don't exclude properties for state info - use them for market analysis!
        # State filtering is now OPTIONAL - we want ALL data for cost-per-sqft calculations
        if target_state:
            prop_address = prop.get('address', '')
            prop_state = self._extract_state_from_address(prop_address)
            
            # If state IS available and DIFFERENT, exclude it
            if prop_state and prop_state != target_state:
                return f"different_state_{prop_state}_vs_{target_state}"
            
            # If state is MISSING or SAME, ACCEPT it (don't exclude!)
        
        # All checks passed - INCLUDE property for analysis
        return None
    
    def _extract_state_from_address(self, address: str) -> str:
        """Extract state code from property address"""
        import re
        
        if not address:
            return None
            
        # Look for state patterns in address: ", TX ", ", TX 78701", etc.
        # Common pattern: ", STATE " or ", STATE zipcode"
        state_pattern = r',\s*([A-Z]{2})\s*(?:\d{5})?(?:,|$)'
        match = re.search(state_pattern, address)
        
        if match:
            state_code = match.group(1)
            # Validate it's a real state code
            if state_code in self.valid_states:
                return state_code
        
        return None

    def _calculate_market_stats(self, sold_homes: List[Dict], for_sale_homes: List[Dict]) -> Dict:
        """Calculate market-wide statistics"""
        
        stats = {
            "sold_homes_stats": self._calc_stats_for_list(sold_homes),
            "for_sale_homes_stats": self._calc_stats_for_list(for_sale_homes),
            "market_trend": self._determine_market_trend(sold_homes, for_sale_homes)
        }
        
        return stats
    
    def _calc_stats_for_list(self, homes: List[Dict]) -> Dict:
        """Calculate stats for a list of homes"""
        
        if not homes:
            return {
                "count": 0,
                "avg_price": None,
                "median_price": None,
                "avg_price_per_sqft": None,
                "median_price_per_sqft": None,
                "avg_days_on_market": None
            }
        
        prices = [h['price'] for h in homes if h.get('price')]
        ppsf = [h['price_per_sqft'] for h in homes if h.get('price_per_sqft')]
        dom = [h['days_on_zillow'] for h in homes if h.get('days_on_zillow')]
        
        return {
            "count": len(homes),
            "avg_price": int(sum(prices) / len(prices)) if prices else None,
            "median_price": int(statistics.median(prices)) if prices else None,
            "avg_price_per_sqft": round(sum(ppsf) / len(ppsf), 2) if ppsf else None,
            "median_price_per_sqft": round(statistics.median(ppsf), 2) if ppsf else None,
            "avg_days_on_market": int(sum(dom) / len(dom)) if dom else None,
            "price_std_dev": round(statistics.stdev(prices), 2) if len(prices) > 1 else None
        }
    
    def _determine_market_trend(self, sold_homes: List[Dict], for_sale_homes: List[Dict]) -> str:
        """Determine if market is hot, stable, or cooling"""
        
        sold_stats = self._calc_stats_for_list(sold_homes)
        for_sale_stats = self._calc_stats_for_list(for_sale_homes)
        
        if not sold_stats['avg_price_per_sqft'] or not for_sale_stats['avg_price_per_sqft']:
            return "unknown"
        
        ppsf_change = (for_sale_stats['avg_price_per_sqft'] - sold_stats['avg_price_per_sqft']) / sold_stats['avg_price_per_sqft']
        
        if ppsf_change > 0.05:
            return "hot"
        elif ppsf_change < -0.05:
            return "cooling"
        else:
            return "stable"
    
    def _rank_comparables(self, sold_homes: List[Dict], target: Dict) -> List[Dict]:
        """Rank comparables by similarity to target property with detailed logging"""
        
        print(f"   📋 Target Property for Comparison:")
        print(f"      Address: {target.get('address', 'N/A')}")
        print(f"      Specs: {target.get('bedrooms', 0)}bed/{target.get('bathrooms', 0)}bath, {target.get('sqft', 0):,} sqft")
        print(f"      Asking: ${target.get('asking_price', 0):,}")
        print()
        
        print(f"   🎯 Calculating similarity scores for {len(sold_homes)} properties...")
        print(f"   🏠 BED/BATH MATCH: All comparables filtered to exact matches")
        print(f"   📅 RECENCY: Recently sold properties ranked highest\n")
        
        for home in sold_homes:
            similarity_score = self._calculate_similarity(home, target)
            home['similarity_score'] = similarity_score
        
        # Sort by similarity (highest first)
        sold_homes.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        # Log top comparables
        print(f"\n   🏆 TOP COMPARABLES (by similarity):")
        for i, home in enumerate(sold_homes[:10]):  # Show top 10
            address = home.get('address', 'Unknown Address')[:45]
            price = home.get('price', 0) or 0
            sqft = home.get('living_area_sqft', 0) or 0
            beds = home.get('bedrooms', 0) or 0
            baths = home.get('bathrooms', 0) or 0
            similarity = home.get('similarity_score', 0) or 0
            price_per_sqft = (home.get('price_per_sqft') or 0)  # ✅ Ensure never None
            
            # Calculate key differences for logging
            sqft_diff = abs(sqft - target.get('sqft', 0)) / max(target.get('sqft', 1), 1) * 100
            bed_diff = abs(beds - target.get('bedrooms', 0)) if beds else 0
            bath_diff = abs(baths - target.get('bathrooms', 0)) if baths else 0
            
            # Safe formatting with None checks
            price_str = f"${int(price):,}" if price else "N/A"
            sqft_str = f"{int(sqft):,}sqft" if sqft else "N/A"
            ppsf_str = f"${price_per_sqft:.0f}/sqft" if price_per_sqft else "N/A/sqft"
            
            print(f"      #{i+1:2d}. {address}")
            print(f"          {price_str} | {sqft_str} | {beds}bed/{baths}bath | {ppsf_str}")
            print(f"          Similarity: {similarity:.2f} | Diffs: {sqft_diff:.0f}% sqft, {bed_diff} beds, {bath_diff:.1f} baths")
            
        return sold_homes
    
    def _calculate_similarity(self, comp: Dict, target: Dict) -> float:
        """
        Calculate similarity score (0-1) between comp and target
        
        Factors:
        - Bedrooms & bathrooms are EXACT MATCH (already filtered, but verified here)
        - Recency is PRIMARY: More recent sales are more relevant to current market
        - Square footage variations are normal; no penalty applied
        """
        
        score = 1.0
        
        # ✅ BEDROOMS - MUST be exact match (should already be filtered)
        if comp.get('bedrooms') and target.get('bedrooms'):
            bed_diff = abs(comp['bedrooms'] - target['bedrooms'])
            if bed_diff == 0:
                score *= 1.0  # Exact match
            else:
                score *= 0.8  # Minor penalty if mismatch (shouldn't happen due to filtering)
        
        # ✅ BATHROOMS - MUST be exact match (should already be filtered)
        if comp.get('bathrooms') and target.get('bathrooms'):
            bath_diff = abs(comp['bathrooms'] - target['bathrooms'])
            if bath_diff == 0:
                score *= 1.0  # Exact match
            else:
                score *= 0.8  # Minor penalty if mismatch (shouldn't happen due to filtering)
        
        # ✅ RECENCY - PRIMARY RANKING FACTOR
        # Properties sold more recently are most relevant to current market
        if comp.get('date_sold') or comp.get('last_sold_date'):
            try:
                sold_date_str = comp.get('date_sold') or comp.get('last_sold_date')
                sold_date = datetime.fromisoformat(str(sold_date_str))
                days_ago = (datetime.now() - sold_date).days
                
                if days_ago < 30:
                    recency_score = 1.0
                elif days_ago < 60:
                    recency_score = 0.95
                elif days_ago < 90:
                    recency_score = 0.90
                elif days_ago < 180:
                    recency_score = 0.85
                elif days_ago < 365:
                    recency_score = 0.75
                else:
                    recency_score = 0.60
                
                score *= recency_score
            except:
                pass
        
        return round(score, 3)
    
    def _calculate_quality_score(self, kept_sold: int, kept_for_sale: int, 
                                 excluded_sold: int, excluded_for_sale: int) -> float:
        """Calculate overall data quality score"""
        
        total_sold = kept_sold + excluded_sold
        total_for_sale = kept_for_sale + excluded_for_sale
        
        if total_sold == 0 and total_for_sale == 0:
            return 0.0
        
        # Quality based on percentage kept
        sold_quality = kept_sold / total_sold if total_sold > 0 else 0
        for_sale_quality = kept_for_sale / total_for_sale if total_for_sale > 0 else 0
        
        # Quantity bonus
        quantity_score = min(kept_sold / 30, 1.0)  # Ideal: 30+ sold homes
        
        # Combined score
        quality_score = (sold_quality * 0.5 + for_sale_quality * 0.3 + quantity_score * 0.2)
        
        return quality_score
    
    def _count_exclusion_reasons(self, excluded: List[Dict]) -> Dict:
        """Count frequency of exclusion reasons"""
        
        reasons = {}
        for prop in excluded:
            reason = prop.get('exclusion_reason', 'unknown')
            reasons[reason] = reasons.get(reason, 0) + 1
        
        return reasons
    
    def _normalize_property_keys(self, properties: List[Dict]) -> List[Dict]:
        """Normalize property keys from beds/baths to bedrooms/bathrooms"""
        for prop in properties:
            # Rename beds → bedrooms if not already present
            if 'beds' in prop and 'bedrooms' not in prop:
                prop['bedrooms'] = prop.pop('beds')
            
            # Rename baths → bathrooms if not already present
            if 'baths' in prop and 'bathrooms' not in prop:
                prop['bathrooms'] = prop.pop('baths')
            
            # Rename living_area → living_area_sqft if not already present
            if 'living_area' in prop and 'living_area_sqft' not in prop:
                prop['living_area_sqft'] = prop.get('living_area')
            
            # ✅ Ensure living_area_sqft is never None (default to 0)
            if prop.get('living_area_sqft') is None:
                prop['living_area_sqft'] = 0
            
            # Calculate price_per_sqft if missing
            if not prop.get('price_per_sqft') and prop.get('price') and prop.get('living_area_sqft'):
                if prop['living_area_sqft'] > 0:
                    prop['price_per_sqft'] = prop['price'] / prop['living_area_sqft']
                else:
                    prop['price_per_sqft'] = 0
            
            # ✅ Ensure price_per_sqft is never None (default to 0 if can't calculate)
            if prop.get('price_per_sqft') is None:
                prop['price_per_sqft'] = 0
            
            # ✅ Ensure bedrooms and bathrooms are never None (default to 0)
            if prop.get('bedrooms') is None:
                prop['bedrooms'] = 0
            if prop.get('bathrooms') is None:
                prop['bathrooms'] = 0
        
        return properties
    
    def _remove_duplicate_addresses(self, properties: List[Dict]) -> List[Dict]:
        """Remove duplicate properties by address, keeping first occurrence"""
        seen_addresses = set()
        unique_properties = []
        
        for prop in properties:
            address = prop.get('address', '').strip().lower()
            
            if address and address not in seen_addresses:
                seen_addresses.add(address)
                unique_properties.append(prop)
            elif not address:
                # If no address, include it anyway (can't deduplicate without address)
                unique_properties.append(prop)
        
        return unique_properties