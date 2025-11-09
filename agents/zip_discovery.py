from typing import List, Dict, Set
import re
from scrapers.duckduckgo_search import DuckDuckGoSearcher
from langchain_groq import ChatGroq
from prompts.zipExtractionPrompt import get_zip_extraction_prompt_template


class ZipDiscoveryAgent:
    """
    Executes DuckDuckGo searches to discover neighboring ZIP codes
    Uses LLM to extract and validate ZIP codes from search results
    """
    
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.1,
            max_tokens=2000
        )
        self.searcher = DuckDuckGoSearcher()
        self.prompt_template = get_zip_extraction_prompt_template()
    
    def discover_zips(self, analysis: Dict) -> Dict:
        """
        Execute searches and discover nearby ZIP codes
        
        Args:
            analysis: Output from QueryAnalysisAgent
        
        Returns:
            Dict with primary ZIP and list of nearby ZIPs
        """
        
        print(f"\n{'='*80}")
        print(f"🗺️  AGENT 2: ZIP Discovery Agent")
        print(f"{'='*80}\n")
        
        primary_zip = analysis['location'].get('zip')
        search_queries = analysis['search_queries']
        
        # Execute all searches
        print(f"📡 Executing {len(search_queries)} DuckDuckGo searches...")
        search_results = self.searcher.get_all_search_results({
            'search_queries': search_queries
        })
        
        print(f"✅ Completed searches\n")
        
        # Extract ZIP codes using LLM
        print("🤖 Extracting ZIP codes from search results...")
        nearby_zips = self._extract_zips_from_results(
            search_results['search_results'],
            primary_zip
        )
        
        # Validate and filter
        validated_zips = self._validate_zips(nearby_zips, primary_zip)
        
        print(f"\n✅ ZIP Discovery Complete:")
        print(f"   Primary ZIP: {primary_zip}")
        print(f"   Nearby ZIPs: {len(validated_zips)}")
        print(f"   Total ZIPs: {len(validated_zips) + 1}")
        print(f"   ZIPs: {', '.join(sorted(validated_zips))}")
        print(f"{'='*80}\n")
        
        return {
            'primary_zip': primary_zip,
            'nearby_zips': sorted(validated_zips),
            'all_zips': [primary_zip] + sorted(validated_zips),
            'total_count': len(validated_zips) + 1
        }
    
    def _extract_zips_from_results(self, search_results: Dict, primary_zip: str) -> Set[str]:
        """Use LLM to extract ZIP codes from search results"""
        
        # Format search results for LLM
        formatted_results = self._format_search_results(search_results)
        
        # Create messages
        messages = self.prompt_template.invoke({
            "search_results_text": formatted_results,
            "primary_zip": primary_zip
        })
        
        # Call LLM
        response = self.llm.invoke(messages)
        
        # Parse extracted ZIPs
        zips = self._parse_zip_extraction(response.content)
        
        return zips
    
    def _format_search_results(self, search_results: Dict) -> str:
        """Format search results for LLM consumption"""
        
        formatted = []
        for i, (query, result) in enumerate(search_results.items(), 1):
            # Truncate to 800 chars per result
            result_text = result[:800] if len(result) > 800 else result
            formatted.append(f"[Search {i}]: {query}\n{result_text}\n")
        
        return "\n".join(formatted)
    
    def _parse_zip_extraction(self, response_text: str) -> Set[str]:
        """Parse ZIP codes from LLM response"""
        
        zips = set()
        
        try:
            # Extract JSON array
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                import json
                zip_list = json.loads(json_match.group())
                zips = set(zip_list)
        except:
            pass
        
        # Also do regex extraction as backup
        zip_matches = re.findall(r'\b(\d{5})\b', response_text)
        zips.update(zip_matches)
        
        return zips
    
    def _validate_zips(self, zips: Set[str], primary_zip: str) -> List[str]:
        """Validate ZIP codes and remove invalid ones"""
        
        validated = []
        
        for zip_code in zips:
            # Skip primary ZIP
            if zip_code == primary_zip:
                continue
            
            # Basic validation: 5 digits, reasonable range
            if len(zip_code) == 5 and zip_code.isdigit():
                zip_int = int(zip_code)
                if 500 <= zip_int <= 99950:
                    validated.append(zip_code)
        
        return validated