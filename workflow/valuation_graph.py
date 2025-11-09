from langgraph.graph import StateGraph, END
from typing import Dict
from datetime import datetime
import time

from workflow.state import RealEstateValuationState
from agents.query_analyzer import QueryAnalysisAgent
from agents.zip_discovery import ZipDiscoveryAgent
from agents.zillow_scraper import ZillowScraperAgent
from agents.data_preprocessor import DataPreprocessorAgent
from agents.valuation_agent import ValuationJudgmentAgent


class RealEstateValuationGraph:
    """
    Complete LangGraph workflow connecting all 5 agents
    """
    
    def __init__(self):
        # Initialize all agents
        self.query_agent = QueryAnalysisAgent()
        self.zip_agent = ZipDiscoveryAgent()
        self.scraper_agent = ZillowScraperAgent()
        self.preprocessor_agent = DataPreprocessorAgent()
        self.valuation_agent = ValuationJudgmentAgent()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow
        
        Flow:
        START → query_analysis → zip_discovery → scraping → preprocessing → valuation → END
        """
        
        workflow = StateGraph(RealEstateValuationState)
        
        # Add nodes (one for each agent)
        workflow.add_node("query_analysis", self._node_query_analysis)
        workflow.add_node("zip_discovery", self._node_zip_discovery)
        workflow.add_node("scraping", self._node_scraping)
        workflow.add_node("preprocessing", self._node_preprocessing)
        workflow.add_node("valuation", self._node_valuation)
        
        # Define edges (linear flow for now)
        workflow.set_entry_point("query_analysis")
        workflow.add_edge("query_analysis", "zip_discovery")
        workflow.add_edge("zip_discovery", "scraping")
        workflow.add_edge("scraping", "preprocessing")
        workflow.add_edge("preprocessing", "valuation")
        workflow.add_edge("valuation", END)
        
        return workflow.compile()
    
    # ==================== NODE FUNCTIONS ====================
    
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
        Scrapes all discovered ZIPs for property data
        """
        
        print(f"\n{'#'*80}")
        print(f"# NODE 3: ZILLOW SCRAPING")
        print(f"{'#'*80}")
        
        try:
            # Get timeframe from query analysis
            timeframe = state['query_analysis'].get('timeframe_months', 6)
            
            # Call Agent 3
            scraped_data = self.scraper_agent.scrape_all_zips(
                state['zip_discovery'],
                timeframe_months=timeframe
            )
            
            # Update state
            state['scraped_data'] = scraped_data
            
            # Check data quality
            if scraped_data['scraping_stats']['total_sold'] < 10:
                state['warnings'].append("Low number of sold homes found (< 10)")
            
            if scraped_data['scraping_stats']['failed_zips'] > 0:
                state['warnings'].append(
                    f"{scraped_data['scraping_stats']['failed_zips']} ZIP codes failed to scrape"
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
    
    # ==================== MAIN EXECUTION ====================
    
    def run(self, user_query: str, target_property: Dict = None) -> Dict:
        """
        Execute the complete workflow
        
        Args:
            user_query: User's input query
            target_property: Optional target property details
        
        Returns:
            Complete workflow results as JSON
        """
        
        print(f"\n{'='*80}")
        print(f"🚀 STARTING REAL ESTATE VALUATION WORKFLOW")
        print(f"{'='*80}")
        print(f"Query: {user_query}")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        
        # Initialize state
        initial_state = {
            "user_query": user_query,
            "target_property": target_property or {},
            "query_analysis": {},
            "zip_discovery": {},
            "scraped_data": {},
            "preprocessed_data": {},
            "valuation_report": {},
            "workflow_start_time": datetime.now().isoformat(),
            "workflow_end_time": "",
            "total_execution_time_seconds": 0.0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
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
                print(f"   • Estimated Value: ${val['estimated_value'].get('mid', 0):,}")
                print(f"   • Range: ${val['estimated_value'].get('low', 0):,} - ${val['estimated_value'].get('high', 0):,}")
                print(f"   • Confidence: {val['confidence'].get('overall_confidence', 'unknown')}")
        
        print(f"{'='*80}\n")