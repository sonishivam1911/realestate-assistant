from langchain_groq import ChatGroq
from prompts.valuationJudgmentPrompt import get_valuation_judgment_prompt_template
from output_parser import ActionParser
import json
import re
from datetime import datetime
from typing import Dict


class ValuationJudgmentAgent:
    """
    Final LLM agent that makes valuation judgment
    Takes preprocessed data and generates comprehensive valuation report
    
    Returns pure JSON output
    """
    
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.2,
            max_tokens=4000
        )
        self.prompt_template = get_valuation_judgment_prompt_template()
        self.parser = ActionParser(use_json_repair=True)  # ✅ Use robust JSON parser
    
    def generate_valuation(self, preprocessed_data: Dict, target_property: Dict) -> Dict:
        """
        Generate final valuation judgment
        
        Args:
            preprocessed_data: Output from DataPreprocessorAgent
            target_property: Target property details
        
        Returns:
            JSON with valuation and market analysis
        """
        
        
        
        print(f"\n{'='*80}")
        print(f"💰 AGENT 5: Valuation Judgment Agent")
        print(f"{'='*80}\n")
        
        # Prepare context for LLM
        context = self._prepare_context(preprocessed_data, target_property)
        
        # Extract asking price from target property
        asking_price = target_property.get('asking_price', 0)
        if isinstance(asking_price, str):
            asking_price = asking_price.replace('$', '').replace(',', '').strip()
        
        asking_price_numeric = float(asking_price) if asking_price else 0
        asking_price_formatted = f"${asking_price_numeric:,.0f}" if asking_price_numeric > 0 else "Unknown"
        
        # Extract target property details
        target_sqft = target_property.get('sqft', 0)
        target_beds = target_property.get('bedrooms', 0)
        target_baths = target_property.get('bathrooms', 0)
        
        print(f"Target Property: {target_property}\n")
        print(f"Asking Price: {asking_price_formatted}\n")
        print(f"Target Square Footage: {target_sqft:,} sqft\n")
        print(f"Target Specs: {target_beds}bed / {target_baths}bath\n")
        print(f"Market Data Context: {context}\n")
        
        # Create messages with asking_price included
        messages = self.prompt_template.invoke({
            "target_property": json.dumps(target_property, indent=2),
            "target_sqft": target_sqft,
            "target_beds": target_beds,
            "target_baths": target_baths,
            "asking_price": asking_price_formatted,
            "asking_price_numeric": asking_price_numeric,
            "market_data": json.dumps(context, indent=2)
        })
        
        # Call LLM
        print("🤖 LLM analyzing market data and making valuation judgment...")
        response = self.llm.invoke(messages)
        
        # Parse JSON response
        valuation = self._parse_valuation_response(response.content)
        
        # Normalize numeric values (LLM may return strings)
        valuation = self._normalize_valuation_numbers(valuation)
        
        # Add metadata
        valuation['valuation_timestamp'] = datetime.now().isoformat()
        valuation['target_property'] = target_property
        
        print(f"\n✅ Valuation Complete:")
        # Safely print estimated value (could be string or number)
        mid_value = valuation.get('estimated_value', {}).get('mid', 0)
        if isinstance(mid_value, str):
            print(f"   • Estimated Value: {mid_value}")
        else:
            print(f"   • Estimated Value: ${mid_value:,}")
        
        # Handle both old and new confidence format
        confidence_level = "unknown"
        if 'confidence' in valuation:
            confidence_level = valuation.get('confidence', {}).get('overall_confidence', 'unknown')
        elif 'analysis_summary' in valuation:
            confidence_level = valuation.get('analysis_summary', {}).get('confidence_level', 'unknown')
        
        print(f"   • Confidence: {confidence_level}")
        
        # Handle both old and new market trend location
        market_trend = "unknown"
        if 'market_analysis' in valuation:
            market_trend = valuation.get('market_analysis', {}).get('pricing_trend', 'unknown')
        
        print(f"   • Market Trend: {market_trend}")
        print(f"{'='*80}\n")
        
        return valuation
    
    def _prepare_context(self, preprocessed_data: Dict, target_property: Dict) -> Dict:
        """Prepare concise context for LLM with TOP 10 COMPARABLES ONLY"""
        
        # ✅ Use SOLD homes first, fallback to FOR-SALE if no SOLD homes available
        # ✅ LIMIT TO TOP 10 ONLY to reduce tokens
        top_comps = preprocessed_data['filtered_sold_homes'][:30]
        
        if not top_comps:
            print("⚠️  No sold homes available, using FOR-SALE properties for market analysis")
            top_comps = preprocessed_data['filtered_for_sale_homes'][:20]
        
        # ✅ SAFETY CHECK: If still no comparables, we have a problem
        if not top_comps:
            print("❌ ERROR: No comparable properties available!")
            return None
        
        # Log what we're sending to the LLM
        print(f"📋 Prepared Context for LLM:")
        print(f"   • Using TOP {len(top_comps)} COMPARABLES (reduced for token efficiency)")
        if top_comps:
            # Show state distribution
            states = {}
            for comp in top_comps:
                address = comp.get('address', '')
                if ', ' in address:
                    parts = address.split(', ')
                    if len(parts) >= 2:
                        state_part = parts[-1].split()[0] if parts[-1] else 'Unknown'
                        states[state_part] = states.get(state_part, 0) + 1
            
            print(f"   • State distribution: {dict(states)}")
            prices = [c.get('price', 0) for c in top_comps if c.get('price')]
            if prices:
                # Convert prices to numbers if they're strings
                numeric_prices = []
                for p in prices:
                    if isinstance(p, str):
                        p = p.replace('$', '').replace(',', '').strip()
                        try:
                            numeric_prices.append(float(p))
                        except ValueError:
                            pass
                    else:
                        numeric_prices.append(float(p))
                
                if numeric_prices:
                    print(f"   • Price range: ${min(numeric_prices):,.0f} - ${max(numeric_prices):,.0f}")
                    print(f"   • Avg price: ${sum(numeric_prices)//len(numeric_prices):,.0f}")
        
        # Summarize comparables with reasoning (COMPACT FORMAT)
        comp_summary = []
        for idx, comp in enumerate(top_comps, 1):
            # Generate concise reasoning
            reasoning_parts = []
            
            similarity = comp.get('similarity_score', 0)
            if similarity > 0.9:
                reasoning_parts.append("Excellent match")
            elif similarity > 0.8:
                reasoning_parts.append("Very similar")
            elif similarity > 0.7:
                reasoning_parts.append("Good match")
            else:
                reasoning_parts.append("Comparable")
            
            # Add price/sqft info (most important)
            comp_ppsf = comp.get('price_per_sqft', 0)
            if comp_ppsf:
                reasoning_parts.append(f"${comp_ppsf:.0f}/sqft")
            
            # Add beds/baths match if exact
            comp_beds = comp.get('bedrooms', 0)
            comp_baths = comp.get('bathrooms', 0)
            
            target_beds = target_property.get('bedrooms', 0)
            target_baths = target_property.get('bathrooms', 0)
            
            if comp_beds == target_beds and comp_baths == target_baths:
                reasoning_parts.append("exact match")
            
            # Add recency
            status = comp.get('home_status', 'for_sale')
            if status == 'sold':
                reasoning_parts.append("sold")
            else:
                reasoning_parts.append("active")
            
            reasoning = " • ".join(reasoning_parts)
            
            comp_summary.append({
                "rank": idx,
                "address": comp.get('address'),
                "price": comp.get('price'),
                "sqft": comp.get('living_area_sqft'),
                "price_per_sqft": comp.get('price_per_sqft'),
                "bedrooms": comp.get('bedrooms'),
                "bathrooms": comp.get('bathrooms'),
                "similarity_score": round(comp.get('similarity_score', 0), 2),
                "status": comp.get('home_status', 'for_sale'),
                "reasoning": reasoning
            })
        
        context = {
            "top_10_comparables": comp_summary,  # ✅ Only top 10 (at least 1, up to 10)
            "market_statistics": preprocessed_data['market_statistics'],
            "total_properties_analyzed": len(preprocessed_data['filtered_sold_homes']) + len(preprocessed_data['filtered_for_sale_homes']),
            "data_quality_score": preprocessed_data['data_quality']['quality_score'],
            "note": f"Using top {len(comp_summary)} most similar properties from market analysis"
        }
    
        
        return context
    
    def _parse_valuation_response(self, response_text: str) -> Dict:
        """
        Parse LLM valuation JSON response using robust ActionParser
        
        ✅ Uses json-repair library to fix malformed JSON
        ✅ Handles missing quotes, trailing commas, unescaped quotes
        ✅ Falls back gracefully if JSON cannot be repaired
        """
        
        try:
            print("\n🔍 Parsing LLM response with ActionParser...")
            
            # Use the robust parser's safe_json_parse method
            parsed_json = self.parser.safe_json_parse(response_text)
            
            if parsed_json and isinstance(parsed_json, dict):
                print(f"✅ Successfully parsed valuation JSON")
                print(f"   Keys found: {list(parsed_json.keys())}\n")
                
                # Handle new prompt structure: action + action_input
                if "action" in parsed_json and "action_input" in parsed_json:
                    print(f"✅ Detected new structure: action={parsed_json['action']}")
                    # Extract the actual valuation from action_input
                    return parsed_json["action_input"]
                else:
                    # Return old structure as-is for backward compatibility
                    return parsed_json
            else:
                print(f"⚠️  Parser returned None or non-dict, using fallback")
                return self._fallback_valuation()
        
        except Exception as e:
            print(f"❌ Parsing error with ActionParser: {e}")
            print(f"   Falling back to basic JSON extraction...")
            
            # Fallback: try basic regex extraction
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    valuation = json.loads(json_str)
                    print(f"✅ Basic extraction succeeded\n")
                    return valuation
            except Exception as e2:
                print(f"❌ Basic extraction also failed: {e2}")
            
            # Final fallback
            return self._fallback_valuation()
    
    def _normalize_valuation_numbers(self, valuation: Dict) -> Dict:
        """
        Convert string numbers to actual numbers in valuation response
        LLM may return "$750,000" as string, needs conversion to float
        """
        def to_number(value):
            """Convert string or number to float, handling currency formatting"""
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = value.replace('$', '').replace(',', '').strip()
                try:
                    return float(cleaned)
                except ValueError:
                    return 0
            return 0
        
        # Normalize estimated_value numbers
        if 'estimated_value' in valuation and isinstance(valuation['estimated_value'], dict):
            for key in ['low', 'mid', 'high', 'recommended_listing_price']:
                if key in valuation['estimated_value']:
                    valuation['estimated_value'][key] = to_number(valuation['estimated_value'][key])
        
        # Normalize asking_price_evaluation numbers if present
        if 'asking_price_evaluation' in valuation and isinstance(valuation['asking_price_evaluation'], dict):
            for key in ['target_asking_price', 'your_mid_estimate']:
                if key in valuation['asking_price_evaluation']:
                    valuation['asking_price_evaluation'][key] = to_number(valuation['asking_price_evaluation'][key])
        
        # Normalize confidence score
        if 'confidence' in valuation and isinstance(valuation['confidence'], dict):
            if 'score' in valuation['confidence']:
                score = valuation['confidence']['score']
                if isinstance(score, str):
                    try:
                        valuation['confidence']['score'] = float(score)
                    except ValueError:
                        valuation['confidence']['score'] = 0
        
        return valuation
    
    def _fallback_valuation(self) -> Dict:
        """Fallback valuation if LLM fails"""
        return {
            "estimated_value": {
                "low": 0,
                "mid": 0,
                "high": 0
            },
            "confidence": {
                "overall_confidence": "low",
                "score": 0.3
            },
            "market_analysis": {
                "trend": "unknown"
            },
            "reasoning": "Valuation failed - insufficient data",
            "error": "LLM response parsing failed"
        }