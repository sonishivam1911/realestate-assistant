from workflow.valuation_graph import RealEstateValuationGraph
import json
from datetime import datetime


def main():
    """
    Main execution - run the complete workflow
    """
    
    # Initialize the workflow
    print("🏗️  Initializing Real Estate Valuation System...")
    workflow = RealEstateValuationGraph()
    print("✅ System ready!\n")
    
    # ============================================
    # EXAMPLE 1: Market Analysis by ZIP Code
    # ============================================
    
    print("\n" + "="*80)
    print("EXAMPLE 1: Market Analysis by ZIP Code")
    print("="*80)
    
    result1 = workflow.run(
        user_query="What's the market like in 78701?",
        target_property=None
    )
    
    # Save results to file
    with open(f"valuation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(result1, f, indent=2)
    
    print("\n✅ Report saved to valuation_report_*.json")
    
    
    # ============================================
    # EXAMPLE 2: Single Property Valuation with Filters
    # ============================================
    
    print("\n" + "="*80)
    print("EXAMPLE 2: Single Property Valuation with Filters")
    print("="*80)
    
    target_property = {
        "address": "199 Hyde Park",
        "city": "Somerset",
        "state": "NJ",
        "zipcode": "08873",
        "bedrooms": 2,
        "bathrooms": 3,
        "sqft": 1400,
        "year_built": 1986,
        "property_type": "Townhouse",
        "asking_price": 350000
    }
    
    # Apply filters for similar properties
    filters = {
        "bedrooms": 2,
        "bathrooms": 3,
        "property_type": "townhouse",
        "min_sqft": 1200,
        "max_sqft": 1600,
        "year_built": 1986
    }
    
    result2 = workflow.run(
        user_query="Value my home at 199 Hyde Park Somerset NJ 08873",
        target_property=target_property,
        filters=filters
    )
    
    # Save results
    with open(f"property_valuation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(result2, f, indent=2)
    
    print("\n✅ Report saved to property_valuation_*.json")
    
    
    # ============================================
    # EXAMPLE 3: Quick Access to Key Results
    # ============================================
    
    print("\n" + "="*80)
    print("KEY RESULTS SUMMARY")
    print("="*80)
    
    if result2.get('valuation_report'):
        valuation = result2['valuation_report']
        
        print(f"\n🏠 PROPERTY: {target_property['address']}, {target_property['city']} {target_property['state']} {target_property['zipcode']}")
        print(f"   Type: {target_property.get('property_type', 'Unknown')} | {target_property.get('bedrooms')}bed / {target_property.get('bathrooms')}bath | {target_property.get('sqft'):,} sqft | Built {target_property.get('year_built')}")
        print(f"   Asking Price: ${target_property['asking_price']:,}")
        
        if 'estimated_value' in valuation:
            est_val = valuation['estimated_value']
            print(f"\n💰 VALUATION:")
            
            # Convert to numbers safely (they may be strings from LLM)
            def to_num(val):
                if isinstance(val, str):
                    val = val.replace('$', '').replace(',', '').strip()
                    try:
                        return float(val)
                    except ValueError:
                        return 0
                return float(val) if val else 0
            
            low_est = to_num(est_val.get('low', 0))
            mid_est = to_num(est_val.get('mid', 0))
            high_est = to_num(est_val.get('high', 0))
            
            print(f"   • Low Estimate: ${low_est:,.0f}")
            print(f"   • Mid Estimate: ${mid_est:,.0f}")
            print(f"   • High Estimate: ${high_est:,.0f}")
            
            # Compare to asking
            mid_val = mid_est
            diff = mid_val - target_property['asking_price']
            diff_pct = (diff / target_property['asking_price'] * 100) if target_property['asking_price'] > 0 else 0
            
            print(f"\n📊 VS ASKING PRICE:")
            print(f"   • Difference: ${diff:,.0f} ({diff_pct:+.1f}%)")
            
            if diff_pct > 5:
                print(f"   • Assessment: UNDERPRICED ✅")
            elif diff_pct < -5:
                print(f"   • Assessment: OVERPRICED ⚠️")
            else:
                print(f"   • Assessment: FAIRLY PRICED ✓")
        
        # Handle both old and new confidence formats
        confidence_level = "unknown"
        confidence_score = 0
        
        if 'confidence' in valuation:
            conf = valuation['confidence']
            confidence_level = conf.get('overall_confidence', 'unknown')
            confidence_score = conf.get('score', 0)
        elif 'analysis_summary' in valuation:
            summary = valuation['analysis_summary']
            confidence_level = summary.get('confidence_level', 'unknown')
            confidence_score = summary.get('confidence_score', 0)
        
        if confidence_level != "unknown":
            print(f"\n🎯 CONFIDENCE:")
            print(f"   • Level: {confidence_level.upper()}")
            print(f"   • Score: {confidence_score*100:.0f}%")
        
        if 'market_analysis' in valuation:
            market = valuation['market_analysis']
            print(f"\n📈 MARKET ANALYSIS:")
            print(f"   • Trend: {market.get('trend', 'unknown').upper()}")
            print(f"   • Inventory: {market.get('inventory_status', 'unknown')}")
            print(f"   • Avg Days on Market: {market.get('days_on_market_avg', 'N/A')}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
