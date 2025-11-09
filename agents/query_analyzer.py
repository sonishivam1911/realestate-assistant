from langchain_groq import ChatGroq
from typing import Dict, List
import json
import re
from prompts.queryAnalysisPrompt import get_query_analysis_prompt_template


class QueryAnalysisAgent:
    """
    Understands user query and generates strategic DuckDuckGo search queries
    to discover nearby ZIP codes for comprehensive market analysis.
    """
    
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.1,
            max_tokens=2000
        )
        self.prompt_template = get_query_analysis_prompt_template()
    
    def analyze_query(self, user_query: str) -> Dict:
        """
        Analyze user query and generate search strategy
        
        Args:
            user_query: Raw user input
        
        Returns:
            Dict with location info and DuckDuckGo search queries
        """
        
        print(f"\n{'='*80}")
        print(f"🧠 AGENT 1: Query Analysis & Search Strategy")
        print(f"{'='*80}\n")
        
        # Create messages
        messages = self.prompt_template.invoke({"user_query": user_query})
        
        # Call LLM
        print("🤖 Analyzing user query and generating search strategy...")
        response = self.llm.invoke(messages)
        
        # Parse response
        analysis = self._parse_analysis_response(response.content)
        
        print(f"\n✅ Analysis Complete:")
        print(f"   Primary Location: {analysis['location']['value']}")
        print(f"   Intent: {analysis['intent']}")
        print(f"   Generated {len(analysis['search_queries'])} search queries")
        print(f"{'='*80}\n")
        
        return analysis
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse LLM JSON response"""
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
        except Exception as e:
            print(f"❌ Analysis error: {e}")
        
        # Fallback
        return self._fallback_analysis()
    
    def _fallback_analysis(self) -> Dict:
        """Fallback if analysis fails"""
        return {
            "location": {
                "type": "unknown",
                "value": "",
                "zip": None,
                "city": None,
                "state": None
            },
            "intent": "market_analysis",
            "search_queries": [
                "ZIP codes near me",
                "neighboring ZIP codes USA"
            ],
            "timeframe_months": 6,
            "confidence": 0.3
        }