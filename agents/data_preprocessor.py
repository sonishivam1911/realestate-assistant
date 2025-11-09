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
        
        sold_homes = scraped_data['sold_homes']
        for_sale_homes = scraped_data['for_sale_homes']
        
        print(f"📥 Input Data:")
        print(f"   • Raw Sold Homes: {len(sold_homes)}")
        print(f"   • Raw For-Sale Homes: {len(for_sale_homes)}\n")
        
        # Filter sold homes
        print("🧹 Filtering sold homes...")
        filtered_sold, sold_excluded = self._filter_properties(sold_homes, target_property)
        print(f"   ✅ Kept: {len(filtered_sold)}")
        print(f"   ❌ Excluded: {len(sold_excluded)}\n")
        
        # Filter for-sale homes  
        print("🧹 Filtering for-sale homes...")
        filtered_for_sale, for_sale_excluded = self._filter_properties(for_sale_homes, target_property)
        print(f"   ✅ Kept: {len(filtered_for_sale)}")
        print(f"   ❌ Excluded: {len(for_sale_excluded)}\n")
        
        # Calculate market statistics
        print("📊 Calculating market statistics...")
        market_stats = self._calculate_market_stats(filtered_sold, filtered_for_sale)
        
        # Rank comparables if target property provided
        if target_property:
            print("🎯 Ranking comparables by similarity...")
            filtered_sold = self._rank_comparables(filtered_sold, target_property)
        
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
    
    def _filter_properties(self, properties: List[Dict], target_property: Dict = None) -> tuple:
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
        
        print(f"   🔍 Analyzing {len(properties)} properties...")
        
        for i, prop in enumerate(properties):
            exclusion_reason = self._should_exclude(prop, target_state)
            
            if exclusion_reason:
                prop['exclusion_reason'] = exclusion_reason
                excluded.append(prop)
                
                # Log excluded properties with details
                if i < 5:  # Show details for first 5 excluded properties
                    address = prop.get('address', 'Unknown Address')[:50]
                    price = prop.get('price', 'N/A')
                    sqft = prop.get('living_area_sqft', 'N/A')
                    print(f"      ❌ {address} - Excluded: {exclusion_reason}")
                    print(f"         Price: {price}, Sqft: {sqft}")
            else:
                filtered.append(prop)
                
                # Log first few accepted properties for transparency
                if len(filtered) <= 5:
                    address = prop.get('address', 'Unknown Address')[:50]
                    price = prop.get('price', 0)
                    sqft = prop.get('living_area_sqft', 0)
                    beds = prop.get('bedrooms', 0)
                    baths = prop.get('bathrooms', 0)
                    price_per_sqft = prop.get('price_per_sqft', 0)
                    print(f"      ✅ {address}")
                    print(f"         ${price:,} | {sqft:,} sqft | {beds}bed/{baths}bath | ${price_per_sqft:.0f}/sqft")
        
        # Log summary of filtering results
        if len(excluded) > 5:
            print(f"      ... and {len(excluded) - 5} more excluded properties")
        
        return filtered, excluded
    
    def _should_exclude(self, prop: Dict, target_state: str = None) -> str:
        """Check if property should be excluded, return reason if yes"""
        
        # Must have price
        price = prop.get('price')
        if not price or (isinstance(price, str) and not price.strip()):
            return "missing_price"

        # Price must be reasonable
        if prop['price'] < self.min_price or prop['price'] > self.max_price:
            return "price_out_of_range"
        
        # Must have square footage
        if not prop.get('living_area_sqft'):
            return "missing_sqft"
        
        # Sqft must be reasonable
        if prop['living_area_sqft'] < self.min_sqft or prop['living_area_sqft'] > self.max_sqft:
            return "sqft_out_of_range"
        
        # Price per sqft must be reasonable (if calculated)
        if prop.get('price_per_sqft'):
            if prop['price_per_sqft'] < 10 or prop['price_per_sqft'] > 5000:
                return "price_per_sqft_outlier"
        
        # Must have basic property info
        if not prop.get('bedrooms') or not prop.get('bathrooms'):
            return "missing_basic_info"
        
        # State filtering - must be in same state as target property
        if target_state:
            prop_address = prop.get('address', '')
            prop_state = self._extract_state_from_address(prop_address)
            
            if not prop_state:
                return "missing_state_info"
            
            if prop_state != target_state:
                return f"different_state_{prop_state}_vs_{target_state}"
        
        # All checks passed
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
        
        for home in sold_homes:
            similarity_score = self._calculate_similarity(home, target)
            home['similarity_score'] = similarity_score
        
        # Sort by similarity (highest first)
        sold_homes.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        # Log top comparables
        print(f"\n   🏆 TOP COMPARABLES (by similarity):")
        for i, home in enumerate(sold_homes[:10]):  # Show top 10
            address = home.get('address', 'Unknown Address')[:45]
            price = home.get('price', 0)
            sqft = home.get('living_area_sqft', 0)
            beds = home.get('bedrooms', 0)
            baths = home.get('bathrooms', 0)
            similarity = home.get('similarity_score', 0)
            price_per_sqft = home.get('price_per_sqft', 0)
            
            # Calculate key differences for logging
            sqft_diff = abs(sqft - target.get('sqft', 0)) / max(target.get('sqft', 1), 1) * 100
            bed_diff = abs(beds - target.get('bedrooms', 0)) if beds else 0
            bath_diff = abs(baths - target.get('bathrooms', 0)) if baths else 0
            
            print(f"      #{i+1:2d}. {address}")
            print(f"          ${price:,} | {sqft:,}sqft | {beds}bed/{baths}bath | ${price_per_sqft:.0f}/sqft")
            print(f"          Similarity: {similarity:.2f} | Diffs: {sqft_diff:.0f}% sqft, {bed_diff} beds, {bath_diff:.1f} baths")
            
        return sold_homes
    
    def _calculate_similarity(self, comp: Dict, target: Dict) -> float:
        """Calculate similarity score (0-1) between comp and target"""
        
        score = 1.0
        
        # Compare square footage (weight: 0.4)
        if comp.get('living_area_sqft') and target.get('sqft'):
            sqft_diff = abs(comp['living_area_sqft'] - target['sqft']) / target['sqft']
            if sqft_diff < 0.1:
                score *= 1.0
            elif sqft_diff < 0.2:
                score *= 0.8
            elif sqft_diff < 0.3:
                score *= 0.6
            else:
                score *= 0.4
        
        # Compare bedrooms (weight: 0.2)
        if comp.get('bedrooms') and target.get('bedrooms'):
            bed_diff = abs(comp['bedrooms'] - target['bedrooms'])
            if bed_diff == 0:
                score *= 1.0
            elif bed_diff == 1:
                score *= 0.8
            else:
                score *= 0.5
        
        # Compare bathrooms (weight: 0.2)
        if comp.get('bathrooms') and target.get('bathrooms'):
            bath_diff = abs(comp['bathrooms'] - target['bathrooms'])
            if bath_diff == 0:
                score *= 1.0
            elif bath_diff <= 0.5:
                score *= 0.9
            else:
                score *= 0.7
        
        # Recency bonus (weight: 0.2)
        if comp.get('date_sold'):
            try:
                sold_date = datetime.fromisoformat(comp['date_sold'])
                days_ago = (datetime.now() - sold_date).days
                if days_ago < 90:
                    score *= 1.0
                elif days_ago < 180:
                    score *= 0.9
                else:
                    score *= 0.7
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