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
        filtered_sold, sold_excluded = self._filter_properties(sold_homes)
        print(f"   ✅ Kept: {len(filtered_sold)}")
        print(f"   ❌ Excluded: {len(sold_excluded)}\n")
        
        # Filter for-sale homes
        print("🧹 Filtering for-sale homes...")
        filtered_for_sale, for_sale_excluded = self._filter_properties(for_sale_homes)
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
    
    def _filter_properties(self, properties: List[Dict]) -> tuple:
        """Filter properties based on data quality"""
        
        filtered = []
        excluded = []
        
        for prop in properties:
            exclusion_reason = self._should_exclude(prop)
            
            if exclusion_reason:
                prop['exclusion_reason'] = exclusion_reason
                excluded.append(prop)
            else:
                filtered.append(prop)
        
        return filtered, excluded
    
    def _should_exclude(self, prop: Dict) -> str:
        """Check if property should be excluded, return reason if yes"""
        
        # Must have price
        if not prop.get('price'):
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
        
        # All checks passed
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
        """Rank comparables by similarity to target property"""
        
        for home in sold_homes:
            similarity_score = self._calculate_similarity(home, target)
            home['similarity_score'] = similarity_score
        
        # Sort by similarity (highest first)
        sold_homes.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
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