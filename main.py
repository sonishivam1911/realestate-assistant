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
    # EXAMPLE 2: Single Property Valuation
    # ============================================
    
    print("\n" + "="*80)
    print("EXAMPLE 2: Single Property Valuation")
    print("="*80)
    
    target_property = {
        "address": "123 Main Street",
        "city": "Austin",
        "state": "TX",
        "zipcode": "78701",
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1800,
        "year_built": 2015,
        "property_type": "Single Family",
        "asking_price": 450000
    }
    
    result2 = workflow.run(
        user_query="Value my home at 123 Main Street Austin TX 78701",
        target_property=target_property
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
        
        print(f"\n🏠 PROPERTY: {target_property['address']}")
        print(f"   Asking Price: ${target_property['asking_price']:,}")
        
        if 'estimated_value' in valuation:
            est_val = valuation['estimated_value']
            print(f"\n💰 VALUATION:")
            print(f"   • Low Estimate: ${est_val.get('low', 0):,}")
            print(f"   • Mid Estimate: ${est_val.get('mid', 0):,}")
            print(f"   • High Estimate: ${est_val.get('high', 0):,}")
            
            # Compare to asking
            mid_val = est_val.get('mid', 0)
            diff = mid_val - target_property['asking_price']
            diff_pct = (diff / target_property['asking_price'] * 100) if target_property['asking_price'] > 0 else 0
            
            print(f"\n📊 VS ASKING PRICE:")
            print(f"   • Difference: ${diff:,} ({diff_pct:+.1f}%)")
            
            if diff_pct > 5:
                print(f"   • Assessment: UNDERPRICED ✅")
            elif diff_pct < -5:
                print(f"   • Assessment: OVERPRICED ⚠️")
            else:
                print(f"   • Assessment: FAIRLY PRICED ✓")
        
        if 'confidence' in valuation:
            conf = valuation['confidence']
            print(f"\n🎯 CONFIDENCE:")
            print(f"   • Level: {conf.get('overall_confidence', 'unknown').upper()}")
            print(f"   • Score: {conf.get('score', 0)*100:.0f}%")
        
        if 'market_analysis' in valuation:
            market = valuation['market_analysis']
            print(f"\n📈 MARKET ANALYSIS:")
            print(f"   • Trend: {market.get('trend', 'unknown').upper()}")
            print(f"   • Inventory: {market.get('inventory_status', 'unknown')}")
            print(f"   • Avg Days on Market: {market.get('days_on_market_avg', 'N/A')}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
