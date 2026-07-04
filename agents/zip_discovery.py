from typing import List, Dict, Set, Optional
import re
from scrapers.duckduckgo_search import DuckDuckGoSearcher
from langchain_groq import ChatGroq
from prompts.zipExtractionPrompt import get_zip_extraction_prompt_template
from output_parser import ActionParser


class ZipDiscoveryAgent:
    """
    Executes DuckDuckGo searches to discover neighboring ZIP codes WITHIN THE SAME STATE
    Uses LLM to extract and validate ZIP codes from search results
    Focuses on 5-6 mile radius for comprehensive local market data
    """
    
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.1,
            max_tokens=2000
        )
        self.searcher = DuckDuckGoSearcher()
        self.prompt_template = get_zip_extraction_prompt_template()
        self.parser = ActionParser(use_json_repair=True)  # ✅ Use robust JSON parser
    
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
        
        # Limit to max 5 most relevant ZIPs - quality over quantity
        most_relevant_zips = self._get_most_relevant_zips(validated_zips, primary_zip, max_count=5)
        
        # Determine actual count for display
        actual_count = len(most_relevant_zips)
        
        print(f"\n✅ ZIP Discovery Complete:")
        print(f"   Primary ZIP: {primary_zip}")
        print(f"   Discovered nearby ZIPs: {len(validated_zips)}")
        print(f"   Selected quality ZIPs: {actual_count}/5 (quality over quantity)")
        print(f"   Total ZIPs for analysis: {actual_count + 1}")
        print(f"   ZIPs: {', '.join([primary_zip] + sorted(most_relevant_zips))}")
        print(f"{'='*80}\n")
        
        return {
            'primary_zip': primary_zip,
            'nearby_zips': sorted(most_relevant_zips),
            'all_zips': [primary_zip] + sorted(most_relevant_zips),
            'total_count': len(most_relevant_zips) + 1
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
            print("\n🔍 Parsing ZIP codes with ActionParser...")
            
            # Use the robust parser's safe_json_parse method
            parsed_json = self.parser.safe_json_parse(response_text)
            
            if parsed_json:
                # Handle both dict with 'zips' key and direct list
                if isinstance(parsed_json, dict):
                    zip_list = parsed_json.get('zips', parsed_json.get('zip_codes', []))
                elif isinstance(parsed_json, list):
                    zip_list = parsed_json
                else:
                    zip_list = []
                
                zips = set(str(z).strip() for z in zip_list if z)
                print(f"✅ Successfully parsed {len(zips)} ZIP codes\n")
            else:
                print(f"⚠️  Parser returned None, falling back to regex extraction")
        
        except Exception as e:
            print(f"❌ Parsing error: {e}")
            print(f"   Falling back to regex extraction...")
        
        # Also do regex extraction as backup
        zip_matches = re.findall(r'\b(\d{5})\b', response_text)
        zips.update(zip_matches)
        
        return zips
    
    def _validate_zips(self, zips: Set[str], primary_zip: str) -> List[str]:
        """Validate ZIP codes and remove invalid ones"""
        
        validated = []
        
        # Get expected state from primary ZIP
        expected_state = self._get_zip_state(primary_zip)
        
        for zip_code in zips:
            # Strip leading zeros and whitespace - convert to proper format
            zip_code = str(zip_code).strip().lstrip('0') or '0'
            zip_code = zip_code.zfill(5)
            
            # Skip primary ZIP
            if zip_code == primary_zip:
                continue
            
            # Basic validation: 5 digits, reasonable range
            if len(zip_code) == 5 and zip_code.isdigit():
                zip_int = int(zip_code)
                if 500 <= zip_int <= 99950:
                    # STRICT state validation - only include same state ZIPs
                    if expected_state:
                        zip_state = self._get_zip_state(zip_code)
                        if zip_state and zip_state.upper() == expected_state.upper():
                            validated.append(zip_code)
                        else:
                            print(f"   ⚠️  Excluding {zip_code} (state mismatch: {zip_state or 'unknown'} vs {expected_state})")
                    else:
                        # If we can't determine primary ZIP state, be conservative and validate primary ZIP first
                        print(f"   ⚠️  Warning: Cannot determine state for primary ZIP {primary_zip}")
                        # Try to at least validate it's not from a completely different region
                        zip_state = self._get_zip_state(zip_code)
                        if zip_state:
                            print(f"   ℹ️  Candidate ZIP {zip_code} is in {zip_state}")
                        validated.append(zip_code)
        
        return validated
    
    def _get_most_relevant_zips(self, zips: List[str], primary_zip: str, max_count: int = 10) -> List[str]:
        """
        Select the most relevant ZIPs based on proximity to primary ZIP
        
        Returns 2-5 good quality ZIPs, not always exactly 5
        
        Args:
            zips: List of validated ZIP codes
            primary_zip: The primary/target ZIP code
            max_count: Maximum number of ZIPs to return (default: 10, capped at 5 for quality)
        
        Returns:
            List of most relevant ZIPs (2-5 quality ZIPs, not forced to always be 5)
        """
        
        # Cap max_count to 5 for quality over quantity
        max_count = min(max_count, 5)
        
        if len(zips) <= 2:
            # If 2 or fewer found, return them all (they're all good quality)
            return zips
        
        if len(zips) <= max_count:
            # If we have 3-5 good ZIPs, return all of them
            return zips
        
        # If we have more than 5, select the 5 closest ones
        # Simple proximity ranking based on ZIP code numeric value
        # ZIPs closer to primary ZIP in numeric value are likely geographically closer
        primary_zip_int = int(primary_zip)
        
        # Calculate distance for each ZIP
        zip_distances = []
        for zip_code in zips:
            try:
                zip_int = int(zip_code)
                distance = abs(zip_int - primary_zip_int)
                zip_distances.append((zip_code, distance))
            except:
                continue
        
        # Sort by distance and take top max_count
        zip_distances.sort(key=lambda x: x[1])
        most_relevant = [z[0] for z in zip_distances[:max_count]]
        
        print(f"\n📍 Proximity-based ZIP selection (quality over quantity):")
        print(f"   Primary ZIP: {primary_zip}")
        print(f"   Total discovered: {len(zips)}")
        print(f"   Selected (closest): {len(most_relevant)}/{max_count}")
        
        return most_relevant
    
    def _get_zip_state(self, zip_code: str) -> Optional[str]:
        """
        Get the state for a ZIP code using ZIP code ranges
        Maps first 3 digits (or first 2 for some ranges) to states
        
        Reference: USPS ZIP Code Ranges by State
        https://pe.usps.com/text/pub28/28apc.htm
        """
        if not zip_code or len(zip_code) != 5:
            return None
        
        try:
            zip_int = int(zip_code)
        except:
            return None
        
        # Comprehensive ZIP code to state mapping by range
        # Format: (min_zip, max_zip): "STATE"
        zip_ranges = {
            # Alabama (35000-36999)
            (35000, 36999): "AL",
            # Alaska (99500-99950)
            (99500, 99950): "AK",
            # Arizona (85000-86999)
            (85000, 86999): "AZ",
            # Arkansas (71600-72999)
            (71600, 72999): "AR",
            # California (90000-96699)
            (90000, 96699): "CA",
            # Colorado (80000-81999)
            (80000, 81999): "CO",
            # Connecticut (06000-06999)
            (6000, 6999): "CT",
            # Delaware (19700-19999)
            (19700, 19999): "DE",
            # Florida (32000-34999)
            (32000, 34999): "FL",
            # Georgia (30000-31999)
            (30000, 31999): "GA",
            # Hawaii (96700-96999)
            (96700, 96999): "HI",
            # Idaho (83200-83999)
            (83200, 83999): "ID",
            # Illinois (60000-62999)
            (60000, 62999): "IL",
            # Indiana (46000-47999)
            (46000, 47999): "IN",
            # Iowa (50000-52999)
            (50000, 52999): "IA",
            # Kansas (66000-67999)
            (66000, 67999): "KS",
            # Kentucky (40000-42799)
            (40000, 42799): "KY",
            # Louisiana (70000-71499)
            (70000, 71499): "LA",
            # Maine (03900-04999)
            (3900, 4999): "ME",
            # Maryland (20600-21999)
            (20600, 21999): "MD",
            # Massachusetts (01000-02799)
            (1000, 2799): "MA",
            # Michigan (48000-49999)
            (48000, 49999): "MI",
            # Minnesota (55000-56799)
            (55000, 56799): "MN",
            # Mississippi (38600-39999)
            (38600, 39999): "MS",
            # Missouri (63000-65999)
            (63000, 65999): "MO",
            # Montana (59000-59999)
            (59000, 59999): "MT",
            # Nebraska (68000-69999)
            (68000, 69999): "NE",
            # Nevada (88900-89999)
            (88900, 89999): "NV",
            # New Hampshire (03000-03899)
            (3000, 3899): "NH",
            # New Jersey (07000-08999)
            (7000, 8999): "NJ",
            # New Mexico (87000-88499)
            (87000, 88499): "NM",
            # New York (10000-14999)
            (10000, 14999): "NY",
            # North Carolina (27000-28999)
            (27000, 28999): "NC",
            # North Dakota (58000-58999)
            (58000, 58999): "ND",
            # Ohio (43000-45999)
            (43000, 45999): "OH",
            # Oklahoma (73000-73999)
            (73000, 73999): "OK",
            # Oregon (97000-97999)
            (97000, 97999): "OR",
            # Pennsylvania (15000-19699)
            (15000, 19699): "PA",
            # Rhode Island (02800-02999)
            (2800, 2999): "RI",
            # South Carolina (29000-29999)
            (29000, 29999): "SC",
            # South Dakota (57000-57999)
            (57000, 57999): "SD",
            # Tennessee (37000-38599)
            (37000, 38599): "TN",
            # Texas (73301-88999)
            (73301, 75999): "TX",
            (75000, 75999): "TX",
            (76000, 79999): "TX",
            (77000, 77999): "TX",
            (78000, 78999): "TX",
            # Utah (84000-84999)
            (84000, 84999): "UT",
            # Vermont (05000-05999)
            (5000, 5999): "VT",
            # Virginia (20100-24999)
            (20100, 24999): "VA",
            # Washington (98000-99499)
            (98000, 99499): "WA",
            # West Virginia (24700-26999)
            (24700, 26999): "WV",
            # Wisconsin (53000-54999)
            (53000, 54999): "WI",
            # Wyoming (82000-83199)
            (82000, 83199): "WY",
        }
        
        # Find matching range
        for (min_zip, max_zip), state in zip_ranges.items():
            if min_zip <= zip_int <= max_zip:
                return state
        
        return None