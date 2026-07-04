from langgraph.graph import StateGraph, END
from typing import Dict, List
from datetime import datetime
import time

from workflow.state import RealEstateValuationState
from agents.query_analyzer import QueryAnalysisAgent
from agents.zip_discovery import ZipDiscoveryAgent
from agents.ultimate_zillow_scrapper import UltimateZillowScraper
from agents.data_preprocessor import DataPreprocessorAgent
from agents.valuation_agent import ValuationJudgmentAgent
from agents.email_generator import EmailGeneratorAgent
from zillow_filter_capture import ZillowFilterCapture


class RealEstateValuationGraph:
    """
    Complete LangGraph workflow connecting all 5 agents
    """
    
    def __init__(self):
        # Initialize all agents
        self.query_agent = QueryAnalysisAgent()
        self.zip_agent = ZipDiscoveryAgent()
        self.scraper = None  # Will be initialized per scraping request
        self.preprocessor_agent = DataPreprocessorAgent()
        self.valuation_agent = ValuationJudgmentAgent()
        self.email_generator = EmailGeneratorAgent()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow
        
        Flow:
        START → filter_capture → query_analysis → zip_discovery → scraping → preprocessing → valuation → END
        
        Node 0 (filter_capture): Captures or loads filter configurations for the target location
        """
        
        workflow = StateGraph(RealEstateValuationState)
        
        # Add nodes (one for each agent + filter capture)
        workflow.add_node("filter_capture", self._node_filter_capture)
        workflow.add_node("query_analysis", self._node_query_analysis)
        workflow.add_node("zip_discovery", self._node_zip_discovery)
        workflow.add_node("scraping", self._node_scraping)
        workflow.add_node("user_selection", self._node_user_selection)
        workflow.add_node("preprocessing", self._node_preprocessing)
        workflow.add_node("valuation", self._node_valuation)
        workflow.add_node("email_generation", self._node_email_generation)
        
        # Define edges with conditional logic for interrupts
        workflow.set_entry_point("filter_capture")
        workflow.add_edge("filter_capture", "query_analysis")
        workflow.add_edge("query_analysis", "zip_discovery")
        workflow.add_edge("zip_discovery", "scraping")
        workflow.add_edge("scraping", "user_selection")
        
        # Conditional edge from user_selection - stop if interrupt, continue if selections made
        workflow.add_conditional_edges(
            "user_selection",
            self._should_continue_after_user_selection,
            {
                "continue": "preprocessing",
                "interrupt": END
            }
        )
        
        workflow.add_edge("preprocessing", "valuation")
        workflow.add_edge("valuation", END)
        
        return workflow.compile()
    
    def _should_continue_after_user_selection(self, state: RealEstateValuationState) -> str:
        """
        Conditional function to decide if workflow should continue after user selection
        """
        if state.get('interrupt_flag'):
            print(f"🔄 CONDITIONAL: Interrupt detected - stopping workflow for user input")
            return "interrupt"
        else:
            print(f"🔄 CONDITIONAL: Properties selected - continuing workflow")
            return "continue"
    
    # ==================== NODE FUNCTIONS ====================
    
    def _node_filter_capture(self, state: RealEstateValuationState) -> RealEstateValuationState:
        """
        Node 0: Filter Capture
        On-demand capture or loading of Zillow filter configurations for the target location
        
        Strategy:
        1. Extract location from target_property
        2. Check if we have pre-captured filter configs for this location
        3. If yes: Load them and continue
        4. If no: Launch browser for user to manually set filters
        5. Store filter URL in state for use by scraper
        """
        
        print(f"\n{'#'*80}")
        print(f"# NODE 0: FILTER CAPTURE")
        print(f"{'#'*80}")
        
        try:
            # Extract location from target_property if available
            target_location = None
            if state.get('target_property'):
                # Try to get zipcode directly
                target_location = state['target_property'].get('zipcode')
                
                # If not found, try location field
                if not target_location:
                    target_location = state['target_property'].get('location')
                
                # If still not found, try to extract from address
                if not target_location and state['target_property'].get('address'):
                    address = state['target_property'].get('address')
                    # Extract ZIP from address (typically last 5 digits after comma)
                    import re
                    zip_match = re.search(r'\b(\d{5})\b', address)
                    if zip_match:
                        target_location = zip_match.group(1)
            
            if not target_location:
                print("⚠️  No target location provided - will use basic search URLs")
                state['filter_config'] = None
                return state
            
            print(f"📍 Target location: {target_location}")
            
            # Initialize filter capture tool
            filter_capturer = ZillowFilterCapture()
            
            # Try to load existing configs
            from pathlib import Path
            import json
            
            config_dir = Path('zillow_configs')
            master_file = config_dir / 'all_filter_urls.json'
            
            existing_configs = {}
            if master_file.exists():
                try:
                    with open(master_file, 'r') as f:
                        all_configs = json.load(f)
                        # Filter configs for this location
                        existing_configs = {
                            cfg['filter_name']: cfg 
                            for cfg in all_configs 
                            if cfg.get('base_location') == target_location
                        }
                except Exception as e:
                    print(f"⚠️  Could not load existing configs: {e}")
            
            # If we found existing configs, use them
            if existing_configs:
                print(f"✅ Found {len(existing_configs)} existing filter configs for {target_location}")
                state['filter_config'] = existing_configs
                return state
            
            # No existing configs - AUTOMATICALLY capture filters
            print(f"\n⚠️  No pre-captured filters found for {target_location}")
            print("   📝 Building filters programmatically...")
            
            # Initialize filter capture tool (for auto-mode, we don't need browser)
            filter_capturer = ZillowFilterCapture()
            
            # Don't init driver for auto_mode - just build and save config
            try:
                filter_name = f"{target_location.replace('/', '_').replace(',', '').replace(' ', '_')}_user_filters"
                print(f"📥 Auto-generating filter config for {target_location}...")
                
                # Pass filters from state to filter capture (auto mode)
                state_filters = state.get('filters', {})
                filter_capturer.capture_filter_url(
                    base_location=target_location,
                    filter_name=filter_name,
                    filters=state_filters,  # ← PASS FILTERS FOR AUTO MODE
                    auto_mode=True  # ← USE AUTO MODE (no user interaction, no browser needed)
                )
                
                # Reload configs to get the newly captured ones
                try:
                    if master_file.exists():
                        with open(master_file, 'r') as f:
                            all_configs = json.load(f)
                            existing_configs = {
                                cfg['filter_name']: cfg 
                                for cfg in all_configs 
                                if cfg.get('base_location') == target_location
                            }
                    state['filter_config'] = existing_configs if existing_configs else None
                    print(f"✅ Filter configs auto-generated and loaded for {target_location}")
                except Exception as e:
                    print(f"⚠️  Could not reload configs: {e}")
                    state['filter_config'] = None
                    
            except Exception as e:
                print(f"⚠️  Error during filter generation: {e}")
                state['filter_config'] = None
            
        except Exception as e:
            print(f"❌ Filter Capture failed: {str(e)}")
            state['errors'].append(f"Filter Capture: {str(e)}")
            state['filter_config'] = None
        
        return state
    
    def _node_query_analysis(self, state: RealEstateValuationState) -> RealEstateValuationState:
        """
        Node 1: Query Analysis Agent
        Understands user query and generates search strategy
        """
        
        print(f"\n{'#'*80}")
        print(f"# NODE 1: QUERY ANALYSIS")
        print(f"{'#'*80}")
        
        try:
            # Call Agent 1
            query_analysis = self.query_agent.analyze_query(state['user_query'])
            
            # Update state
            state['query_analysis'] = query_analysis
            
        except Exception as e:
            print(f"❌ Query Analysis failed: {str(e)}")
            state['errors'].append(f"Query Analysis: {str(e)}")
            # Provide fallback
            state['query_analysis'] = {
                "location": {"type": "unknown", "value": ""},
                "intent": "market_analysis",
                "search_queries": [],
                "timeframe_months": 6
            }
        
        return state
    
    def _node_zip_discovery(self, state: RealEstateValuationState) -> RealEstateValuationState:
        """
        Node 2: ZIP Discovery Agent
        Executes DuckDuckGo searches to find nearby ZIPs
        """
        
        print(f"\n{'#'*80}")
        print(f"# NODE 2: ZIP DISCOVERY")
        print(f"{'#'*80}")
        
        try:
            # Call Agent 2
            zip_discovery = self.zip_agent.discover_zips(state['query_analysis'])
            
            # Update state
            state['zip_discovery'] = zip_discovery
            
            # Check if we found any ZIPs
            if not zip_discovery.get('primary_zip'):
                state['warnings'].append("No primary ZIP code found")
            
            if len(zip_discovery.get('all_zips', [])) == 0:
                state['warnings'].append("No ZIPs discovered - will have limited data")
        
        except Exception as e:
            print(f"❌ ZIP Discovery failed: {str(e)}")
            state['errors'].append(f"ZIP Discovery: {str(e)}")
            # Provide fallback
            state['zip_discovery'] = {
                "primary_zip": None,
                "nearby_zips": [],
                "all_zips": [],
                "total_count": 0
            }
        
        return state
    
    def _node_scraping(self, state: RealEstateValuationState) -> RealEstateValuationState:
        """
        Node 3: Zillow Scraper Agent
        Scrapes all discovered ZIPs for property data using production-ready undetected-chromedriver
        """
        
        print(f"\n{'#'*80}")
        print(f"# NODE 3: ZILLOW SCRAPING (Production Ready)")
        print(f"{'#'*80}")
        
        try:
            # Get timeframe from query analysis
            timeframe = state['query_analysis'].get('timeframe_months', 6)
            all_zips = state['zip_discovery'].get('all_zips', [])
            filters = state.get('filters', {})
            
            # Extract filter parameters
            # Use one less bedroom/bathroom for broader search
            target_beds = filters.get('bedrooms')
            target_baths = filters.get('bathrooms')
            
            # For search: use one less bed/bath to cast wider net
            search_beds = target_beds - 1 if target_beds and target_beds > 1 else target_beds
            search_baths = target_baths - 1 if target_baths and target_baths > 1 else target_baths
            
            property_type = filters.get('property_type', 'townhouse').lower()
            min_price = filters.get('min_price')
            max_price = filters.get('max_price')
            year_built = filters.get('year_built')
            
            if filters:
                print(f"🔍 Applied Filters:")
                if target_beds:
                    print(f"   • Target Bedrooms: {target_beds}")
                    print(f"   • Search Bedrooms: {search_beds} (one less for broader results)")
                if target_baths:
                    print(f"   • Target Bathrooms: {target_baths}")
                    print(f"   • Search Bathrooms: {search_baths} (one less for broader results)")
                if property_type:
                    print(f"   • Property Type: {property_type}")
                if min_price or max_price:
                    print(f"   • Price Range: ${min_price or '0':,} - ${max_price or '∞':,}")
                if year_built:
                    print(f"   • Year Built: {year_built}")
            
            if not all_zips:
                state['warnings'].append("No ZIPs to scrape")
                state['scraped_data'] = {
                    "sold_homes": [],
                    "for_sale_homes": [],
                    "scraping_stats": {
                        "total_sold": 0,
                        "total_for_sale": 0,
                        "successful_zips": 0,
                        "failed_zips": 0
                    }
                }
                return state
            
            all_sold = []
            all_for_sale = []
            stats = {
                'total_zips': len(all_zips),
                'successful_zips': 0,
                'failed_zips': 0,
                'total_for_sale': 0,
                'total_sold': 0
            }
            
            for idx, zip_code in enumerate(all_zips, 1):
                try:
                    print(f"\n[{idx}/{len(all_zips)}] Processing ZIP: {zip_code}")
                    
                    # Scrape FOR-SALE properties first (max 2 pages for efficiency)
                    self.scraper = UltimateZillowScraper(headless=False)
                    
                    if not self.scraper.init_driver():
                        print(f"   ❌ Failed to initialize driver for ZIP {zip_code}")
                        stats['failed_zips'] += 1
                        time.sleep(2)
                        continue
                    
                    # Build FOR-SALE search URL with filter support
                    # UltimateZillowScraper has intelligent filter URL building
                    search_url = self.scraper.build_zillow_url(
                        zip_code=zip_code,
                        status="for_sale",
                        property_type=property_type,
                        min_beds=search_beds,
                        min_baths=search_baths,
                        min_price=min_price,
                        max_price=max_price
                    )
                    print(f"   🔍 Searching FOR-SALE: {search_url}")
                    
                    # Fetch multiple pages for better data coverage
                    property_urls = self.scraper.get_property_urls_from_search(
                        search_url=search_url,
                        max_pages=2
                    )
                    
                    if not property_urls:
                        print(f"   ⚠️  No FOR-SALE properties found for this ZIP")
                        stats['failed_zips'] += 1
                        self.scraper.cleanup()
                        time.sleep(2)
                        continue
                    
                    print(f"   📍 Found {len(property_urls)} FOR-SALE property links")
                    
                    # Limit properties per ZIP to avoid excessive scraping
                    property_urls = property_urls[:15]
                    
                    # Extract details from FOR-SALE properties
                    for_sale_properties = []  # ✅ Separate list for for-sale
                    for prop_idx, url in enumerate(property_urls, 1):
                        try:
                            prop_data = self.scraper.extract_property_details(url, retry_count=1)
                            if prop_data:
                                # ✅ VALIDATE PROPERTY TYPE MATCHES FILTER
                                if self._validate_property_type(prop_data, property_type):
                                    for_sale_properties.append(prop_data)
                                    print(f"      ✓ Property {prop_idx}/{len(property_urls)}: {prop_data.get('address', 'Unknown')} ({prop_data.get('home_type', 'Unknown')})")
                                else:
                                    home_type = prop_data.get('home_type', 'Unknown')
                                    print(f"      ⊘ Property {prop_idx}/{len(property_urls)}: FILTERED OUT - Type is '{home_type}' (wanted '{property_type}')")
                            else:
                                print(f"      ✗ Property {prop_idx}/{len(property_urls)}: Failed to extract - STOPPING THIS ZIP CODE")
                                break  # ✅ STOP IMMEDIATELY - save what we have and move to next ZIP
                        except Exception as e:
                            print(f"      ✗ Property {prop_idx}/{len(property_urls)}: Error - {str(e)[:50]} - STOPPING THIS ZIP CODE")
                            break  # ✅ STOP IMMEDIATELY - save what we have and move to next ZIP
                        
                        time.sleep(1.5)  # Rate limiting between properties
                    
                    # Add for-sale properties to main list
                    for prop in for_sale_properties:
                        all_for_sale.append(prop)
                    
                    # ✅ NOW SCRAPE SOLD PROPERTIES with correct Zillow format
                    print(f"   🏡 Now scraping SOLD properties (using proper Zillow structure)...")
                    
                    # Initialize sold_properties list at the right scope
                    sold_properties = []
                    
                    # Build SOLD search URL with correct Zillow format
                    sold_search_url = self.scraper.build_zillow_url(
                        zip_code=zip_code,
                        status="sold",
                        property_type=property_type,  
                        min_beds=search_beds,         
                        min_baths=search_baths,       
                        min_price=min_price,          
                        max_price=max_price,
                        days_back=None  # Use Zillow's default timeframe
                    )
                    print(f"   🔍 Searching SOLD: {sold_search_url}")
                    
                    # Get sold property URLs
                    sold_property_urls = self.scraper.get_property_urls_from_search(
                        search_url=sold_search_url,
                        max_pages=2
                    )
                    
                    if sold_property_urls:
                        print(f"   📍 Found {len(sold_property_urls)} SOLD property links")
                        
                        # Limit sold properties per ZIP 
                        sold_property_urls = sold_property_urls[:10]  # Reduced for efficiency
                        
                        # Extract details from SOLD properties
                        for prop_idx, url in enumerate(sold_property_urls, 1):
                            try:
                                prop_data = self.scraper.extract_property_details(url, retry_count=1)
                                if prop_data:
                                    # ✅ VALIDATE PROPERTY TYPE MATCHES FILTER
                                    if self._validate_property_type(prop_data, property_type):
                                        sold_properties.append(prop_data)
                                        print(f"      ✓ SOLD Property {prop_idx}/{len(sold_property_urls)}: {prop_data.get('address', 'Unknown')} ({prop_data.get('home_type', 'Unknown')})")
                                    else:
                                        home_type = prop_data.get('home_type', 'Unknown')
                                        print(f"      ⊘ SOLD Property {prop_idx}/{len(sold_property_urls)}: FILTERED OUT - Type is '{home_type}' (wanted '{property_type}')")
                                else:
                                    print(f"      ✗ SOLD Property {prop_idx}/{len(sold_property_urls)}: Failed to extract")
                            except Exception as e:
                                print(f"      ✗ SOLD Property {prop_idx}/{len(sold_property_urls)}: Error - {str(e)[:50]}")
                            
                            time.sleep(1.5)  # Rate limiting between properties
                        
                        # Add sold properties to main list
                        for prop in sold_properties:
                            all_sold.append(prop)
                        
                        # Update stats for sold properties
                        if len(sold_properties) > 0:
                            stats['total_sold'] += len(sold_properties)
                            print(f"   ✅ SUCCESS: Extracted {len(sold_properties)} SOLD properties")
                        else:
                            print(f"   ⚠️  No SOLD properties extracted for this ZIP")
                    else:
                        print(f"   ⚠️  No SOLD properties found for this ZIP")
                    
                    # Summary for this ZIP (overall success if we got ANY properties)
                    total_properties_extracted = len(for_sale_properties) + len(sold_properties)
                    
                    if total_properties_extracted > 0:
                        # Only increment successful_zips once per ZIP, regardless of property types
                        print(f"   ✅ ZIP COMPLETE: Total {total_properties_extracted} properties extracted")
                    else:
                        print(f"   ⚠️  ZIP FAILED: No properties extracted")
                    
                    # Cleanup after each ZIP
                    self.scraper.cleanup()
                    time.sleep(2)
                        
                except Exception as e:
                    print(f"   ❌ ERROR scraping ZIP {zip_code}: {str(e)[:100]}")
                    # ✅ Save whatever we extracted before the error, then move to next ZIP
                    total_extracted = 0
                    if 'for_sale_properties' in locals() and len(for_sale_properties) > 0:
                        # We got some for-sale properties before the error - save them!
                        for prop in for_sale_properties:
                            all_for_sale.append(prop)
                        stats['total_for_sale'] += len(for_sale_properties)
                        total_extracted += len(for_sale_properties)
                        print(f"   ⚠️  Saved {len(for_sale_properties)} FOR-SALE properties before error")
                    
                    if 'sold_properties' in locals() and len(sold_properties) > 0:
                        # We got some sold properties before the error - save them!
                        for prop in sold_properties:
                            all_sold.append(prop)
                        stats['total_sold'] += len(sold_properties)
                        total_extracted += len(sold_properties)
                        print(f"   ⚠️  Saved {len(sold_properties)} SOLD properties before error")
                    
                    if total_extracted > 0:
                        stats['successful_zips'] += 1
                        print(f"   ⚠️  Partial success: Saved {total_extracted} total properties before error")
                    else:
                        stats['failed_zips'] += 1
                        print(f"   ⚠️  Failed to extract any properties from this ZIP")
                    
                    try:
                        if self.scraper:
                            self.scraper.cleanup()
                    except:
                        pass
                    time.sleep(3)
                    # ✅ Continue to next ZIP - don't break!
            
            # ✅ Final statistics calculation
            total_properties = len(all_for_sale) + len(all_sold)
            stats['successful_zips'] = len([zip_code for zip_code in all_zips if any(prop.get('zipcode') == zip_code for prop in all_for_sale + all_sold)])
            stats['failed_zips'] = stats['total_zips'] - stats['successful_zips']
            
            print(f"\n{'='*80}")
            print(f"🏁 SCRAPING SUMMARY:")
            print(f"   📊 Total ZIPs processed: {stats['total_zips']}")
            print(f"   ✅ Successful ZIPs: {stats['successful_zips']}")
            print(f"   ❌ Failed ZIPs: {stats['failed_zips']}")
            print(f"   🏠 FOR-SALE properties: {stats['total_for_sale']}")
            print(f"   🏡 SOLD properties: {stats['total_sold']}")
            print(f"   📈 Total properties: {total_properties}")
            print(f"{'='*80}\n")
            
            # Update state
            state['scraped_data'] = {
                "primary_zip": state['zip_discovery'].get('primary_zip'),
                "sold_homes": all_sold,
                "for_sale_homes": all_for_sale,
                "scraping_stats": stats,
                "scraper_type": "undetected-chromedriver (FOR-SALE + SOLD)"
            }
            
            # Check data quality
            if stats['total_for_sale'] < 5:
                state['warnings'].append("Low number of FOR-SALE properties found (< 5)")
            
            if stats['total_sold'] < 5:
                state['warnings'].append("Low number of SOLD properties found (< 5) - valuation may be less accurate")
            
            if stats['failed_zips'] > 0:
                state['warnings'].append(
                    f"{stats['failed_zips']} ZIP codes failed to scrape"
                )
        
        except Exception as e:
            print(f"❌ Scraping failed: {str(e)}")
            state['errors'].append(f"Scraping: {str(e)}")
            # Provide fallback
            state['scraped_data'] = {
                "sold_homes": [],
                "for_sale_homes": [],
                "scraping_stats": {
                    "total_sold": 0,
                    "total_for_sale": 0,
                    "successful_zips": 0,
                    "failed_zips": 0
                }
            }
        
        finally:
            # Final cleanup
            try:
                if self.scraper and self.scraper.driver:
                    self.scraper.cleanup()
            except:
                pass
        
        return state
    
    def _node_user_selection(self, state: RealEstateValuationState) -> RealEstateValuationState:
        """
        Node 3.5: User Selection (Interrupt Point)
        """
        from langgraph.types import interrupt
    
        try:
            for_sale_homes = state['scraped_data'].get('for_sale_homes', [])
            
            if not for_sale_homes:
                print("⚠️  No properties found from scraping")
                state['selected_properties'] = []
                return state
        
            
            # Check if selections already exist
            selected = state.get('selected_properties', [])
            
            if selected and len(selected) > 0:
                print(f"✅ {len(selected)} properties already selected by user")
                return state
            
            # Use LangGraph's interrupt() - this actually pauses execution
            user_input = interrupt({
                "message": "Please select properties to continue",
                "available_properties": for_sale_homes,
                "total_count": len(for_sale_homes)
            })
            
            # When resumed, user_input will contain the selected properties
            state['selected_properties'] = user_input.get('selected_properties', [])

        except Exception as e:
            print(f"❌ User selection error: {str(e)}")
            state['errors'].append(f"User Selection: {str(e)}")
            state['selected_properties'] = []
        
        return state
    
    def _node_preprocessing(self, state: RealEstateValuationState) -> RealEstateValuationState:
        """
        Node 4: Data Preprocessing Agent
        Filters and cleans scraped data
        """
        
        print(f"\n{'#'*80}")
        print(f"# NODE 4: DATA PREPROCESSING")
        print(f"{'#'*80}")
        
        try:
            # Call Agent 4
            preprocessed_data = self.preprocessor_agent.preprocess_data(
                state['scraped_data'],
                state.get('target_property')
            )
            
            # Update state
            state['preprocessed_data'] = preprocessed_data
            
            # Check if we have enough data for valuation
            if preprocessed_data['data_quality']['total_sold_kept'] < 5:
                state['warnings'].append("Very low comparable count (< 5) - valuation may be unreliable")
            
            if preprocessed_data['data_quality']['quality_score'] < 0.5:
                state['warnings'].append("Low data quality score - results may be inaccurate")
        
        except Exception as e:
            print(f"❌ Preprocessing failed: {str(e)}")
            state['errors'].append(f"Preprocessing: {str(e)}")
            # Provide fallback
            state['preprocessed_data'] = {
                "filtered_sold_homes": [],
                "filtered_for_sale_homes": [],
                "market_statistics": {},
                "data_quality": {
                    "quality_score": 0.0,
                    "total_sold_kept": 0
                }
            }
        
        return state
    
    def _node_valuation(self, state: RealEstateValuationState) -> RealEstateValuationState:
        """
        Node 5: Valuation Judgment Agent
        LLM makes final valuation judgment
        """
        
        print(f"\n{'#'*80}")
        print(f"# NODE 5: VALUATION JUDGMENT")
        print(f"{'#'*80}")
        
        try:
            # Get target property info
            target_property = state.get('target_property', {})
            
            # If no target property provided, create a default one from query
            if not target_property:
                target_property = {
                    "location": state['query_analysis']['location']['value'],
                    "zipcode": state['zip_discovery'].get('primary_zip'),
                    "intent": state['query_analysis']['intent']
                }
            
            # Call Agent 5
            valuation_report = self.valuation_agent.generate_valuation(
                state['preprocessed_data'],
                target_property
            )
            
            print(f"Valuation Report: {valuation_report}\n")
            
            # Update state
            state['valuation_report'] = valuation_report
            
        except Exception as e:
            print(f"❌ Valuation failed: {str(e)}")
            state['errors'].append(f"Valuation: {str(e)}")
            # Provide fallback
            state['valuation_report'] = {
                "estimated_value": {
                    "low": 0,
                    "mid": 0,
                    "high": 0
                },
                "confidence": {
                    "overall_confidence": "low",
                    "score": 0.0
                },
                "reasoning": {
                    "valuation_logic": "Valuation failed due to insufficient data"
                },
                "error": str(e)
            }
        
        return state
    
    def _node_email_generation(self, state: RealEstateValuationState) -> RealEstateValuationState:
        """
        Node 6: Email Generation Agent
        Generates professional client email from valuation analysis
        """
        
        print(f"\n{'#'*80}")
        print(f"# NODE 6: EMAIL GENERATION")
        print(f"{'#'*80}")
        
        try:
            recipient_name = state.get('email_recipient_name', 'Valued Client')
            
            if not recipient_name or recipient_name == '':
                recipient_name = 'Valued Client'
            
            # Call Email Generator Agent
            email_data = self.email_generator.generate_email(state, recipient_name)
            
            # Update state
            state['email_data'] = email_data
            
            print(f"✅ Email generated successfully")
            
        except Exception as e:
            print(f"❌ Email generation failed: {str(e)}")
            state['errors'].append(f"Email Generation: {str(e)}")
            # Provide fallback
            state['email_data'] = {
                "subject": "Property Valuation Report",
                "body": "Email generation encountered an error. Please contact support.",
                "recipient_name": state.get('email_recipient_name', 'Valued Client'),
                "property_address": state.get('target_property', {}).get('address', 'Unknown'),
                "estimated_value": "N/A",
                "comparable_count": 0,
                "confidence_level": "Unknown"
            }
        
        return state
    
    # ==================== HELPER METHODS ====================
    
    def _validate_property_type(self, property_data: Dict, filter_type: str) -> bool:
        """
        Validate if a property matches the requested type
        
        Simple mapping:
        - "single family" → search for house types (handles SINGLE_FAMILY, House, etc.)
        - "multi family" → search for multi-family types (handles MULTI_FAMILY, etc.)
        - "condos" → search for condo types
        
        Args:
            property_data: Property data dict with 'home_type' field
            filter_type: Requested property type (e.g., 'single family', 'multi family', 'condos')
        
        Returns:
            True if property matches type, False otherwise
        """
        if not filter_type:
            return True  # No filter specified, accept all
        
        # Normalize both to lowercase and replace underscores with spaces for comparison
        home_type = property_data.get('home_type', '').lower().replace('_', ' ')
        filter_type_lower = filter_type.lower().replace('_', ' ')
        
        # ✅ Simple mapping as requested
        if 'single family' in filter_type_lower:
            # Accept only house types (handles: SINGLE_FAMILY, House, Single Family, etc.)
            allowed_types = ['house', 'single family']
            return any(allowed in home_type for allowed in allowed_types)
        
        elif 'multi family' in filter_type_lower:
            # Accept multi-family, apartment buildings, duplexes, etc.
            # Handles: MULTI_FAMILY, Multi Family, Apartment, Duplex, etc.
            allowed_types = ['multi family', 'apartment', 'duplex', 'triplex', 'fourplex']
            return any(allowed in home_type for allowed in allowed_types)
        
        elif 'condo' in filter_type_lower:
            # Accept only condo/condominium types (NOT apartments or multi-family)
            allowed_types = ['condo', 'condominium']
            return any(allowed in home_type for allowed in allowed_types)
        
        else:
            # For any other type, accept it as-is
            return True
    
    # ==================== MAIN EXECUTION ====================
    
    def run(self, user_query: str, target_property: Dict = None, filters: Dict = None, email_recipient_name: str = None, selected_properties: List = None) -> Dict:
        """
        Execute the complete workflow
        
        Args:
            user_query: User's input query
            target_property: Optional target property details
            filters: Optional filters dict with bedrooms, bathrooms, property_type, sqft, year_built, etc.
            email_recipient_name: Name of email recipient (client name) for email generation
        
        Returns:
            Complete workflow results as JSON
        """
        
        print(f"\n{'='*80}")
        print(f"🚀 STARTING REAL ESTATE VALUATION WORKFLOW")
        print(f"{'='*80}")
        print(f"Query: {user_query}")
        if filters:
            print(f"Filters: {filters}")
        if email_recipient_name:
            print(f"Email Recipient: {email_recipient_name}")
        if selected_properties:
            print(f"🔍 DEBUG: SELECTED PROPERTIES PROVIDED: {len(selected_properties)} properties")
            for i, prop in enumerate(selected_properties[:3]):
                print(f"   Property {i+1}: {prop.get('address', 'N/A')[:40]}")
        else:
            print(f"🔍 DEBUG: NO SELECTED PROPERTIES PROVIDED - will trigger interrupt")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        
        # Initialize state
        initial_state = {
            "user_query": user_query,
            "target_property": target_property or {},
            "filters": filters or {},
            "email_recipient_name": email_recipient_name or "Valued Client",
            "selected_properties": selected_properties or [],
            "query_analysis": {},
            "zip_discovery": {},
            "scraped_data": {},
            "preprocessed_data": {},
            "valuation_report": {},
            "email_data": {},
            "workflow_start_time": datetime.now().isoformat(),
            "workflow_end_time": "",
            "total_execution_time_seconds": 0.0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Run the graph with interrupt checking
            final_state = self.graph.invoke(initial_state)
            
            # Check if we hit an interrupt
            if final_state.get('interrupt_flag'):
                print(f"\n⏸️  WORKFLOW INTERRUPTED - returning partial state for UI")
                print(f"   Interrupt reason: User property selection required")
                print(f"   Available properties: {len(final_state.get('available_properties', []))}")
                return final_state
            
            # Calculate execution time
            end_time = time.time()
            final_state['workflow_end_time'] = datetime.now().isoformat()
            final_state['total_execution_time_seconds'] = round(end_time - start_time, 2)
            
            # Print summary
            self._print_summary(final_state)
            
            return final_state
        
        except Exception as e:
            print(f"\n❌ WORKFLOW FAILED: {str(e)}")
            initial_state['errors'].append(f"Workflow: {str(e)}")
            return initial_state
    
    def _print_summary(self, state: Dict):
        """Print workflow summary"""
        
        print(f"\n{'='*80}")
        print(f"✅ WORKFLOW COMPLETE")
        print(f"{'='*80}")
        print(f"Execution Time: {state['total_execution_time_seconds']}s")
        
        if state['errors']:
            print(f"\n❌ ERRORS ({len(state['errors'])}):")
            for error in state['errors']:
                print(f"   • {error}")
        
        if state['warnings']:
            print(f"\n⚠️  WARNINGS ({len(state['warnings'])}):")
            for warning in state['warnings']:
                print(f"   • {warning}")
        
        # Print key results
        if state.get('valuation_report'):
            val = state['valuation_report']
            if 'estimated_value' in val:
                print(f"\n💰 VALUATION RESULTS:")
                
                # Handle estimated_value safely (may be string or number)
                mid_val = val['estimated_value'].get('mid', 0)
                low_val = val['estimated_value'].get('low', 0)
                high_val = val['estimated_value'].get('high', 0)
                
                # Convert to float if string
                if isinstance(mid_val, str):
                    mid_val = float(mid_val.replace('$', '').replace(',', ''))
                if isinstance(low_val, str):
                    low_val = float(low_val.replace('$', '').replace(',', ''))
                if isinstance(high_val, str):
                    high_val = float(high_val.replace('$', '').replace(',', ''))
                
                print(f"   • Estimated Value: ${mid_val:,.0f}")
                print(f"   • Range: ${low_val:,.0f} - ${high_val:,.0f}")
                
                # Handle confidence - new format has it in analysis_summary
                confidence_str = "unknown"
                if 'confidence' in val:
                    confidence_str = val['confidence'].get('overall_confidence', 'unknown')
                elif 'analysis_summary' in val:
                    confidence_str = val['analysis_summary'].get('confidence_level', 'unknown')
                
                print(f"   • Confidence: {confidence_str}")
        
        # Print email summary
        if state.get('email_data'):
            email = state['email_data']
            print(f"\n📧 EMAIL SUMMARY:")
            print(f"   • Subject: {email.get('subject', 'N/A')}")
            print(f"   • Body Length: {len(email.get('body', '')) } characters")
        
        print(f"{'='*80}\n")