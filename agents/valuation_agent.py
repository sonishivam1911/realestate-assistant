from langchain_groq import ChatGroq
from prompts.valuationJudgmentPrompt import get_valuation_judgment_prompt_template
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
        
        print(f"Target Property: {target_property}\n")
        print(f"Market Data Context: {context}\n")
        
        # Create messages
        messages = self.prompt_template.invoke({
            "target_property": json.dumps(target_property, indent=2),
            "market_data": json.dumps(context, indent=2)
        })
        
        # Call LLM
        print("🤖 LLM analyzing market data and making valuation judgment...")
        response = self.llm.invoke(messages)
        
        # Parse JSON response
        valuation = self._parse_valuation_response(response.content)
        
        # Add metadata
        valuation['valuation_timestamp'] = datetime.now().isoformat()
        valuation['target_property'] = target_property
        
        print(f"\n✅ Valuation Complete:")
        print(f"   • Estimated Value: ${valuation['estimated_value']['mid']:,}")
        print(f"   • Confidence: {valuation['confidence']['overall_confidence']}")
        print(f"   • Market Trend: {valuation['market_analysis']['trend']}")
        print(f"{'='*80}\n")
        
        return valuation
    
    def _prepare_context(self, preprocessed_data: Dict, target_property: Dict) -> Dict:
        """Prepare concise context for LLM"""
        
        # Take top 20 comparables (already ranked if target property was provided)
        top_comps = preprocessed_data['filtered_sold_homes'][:20]
        
        # Log what we're sending to the LLM
        print(f"📋 Prepared Context for LLM:")
        print(f"   • Using {len(top_comps)} top comparables")
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
            print(f"   • Price range: ${min(c.get('price', 0) for c in top_comps):,} - ${max(c.get('price', 0) for c in top_comps):,}")
        
        # Summarize comparables
        comp_summary = []
        for comp in top_comps:
            comp_summary.append({
                "address": comp.get('address'),
                "price": comp.get('price'),
                "sqft": comp.get('living_area_sqft'),
                "price_per_sqft": comp.get('price_per_sqft'),
                "bedrooms": comp.get('bedrooms'),
                "bathrooms": comp.get('bathrooms'),
                "date_sold": comp.get('date_sold'),
                "days_on_market": comp.get('days_on_zillow'),
                "similarity_score": comp.get('similarity_score')
            })
        
        context = {
            "comparables": comp_summary,
            "market_statistics": preprocessed_data['market_statistics'],
            "data_quality": preprocessed_data['data_quality']
        }
    
        
        return context
    
    def _parse_valuation_response(self, response_text: str) -> Dict:
        """Parse LLM valuation JSON response"""
        
        try:
            # Extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                valuation = json.loads(json_str)
                print(f"Parsed Valuation JSON: {valuation}\n")
                return valuation
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
        except Exception as e:
            print(f"❌ Valuation parsing error: {e}")
        
        # Fallback
        return self._fallback_valuation()
    
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