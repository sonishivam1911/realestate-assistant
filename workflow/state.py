from typing import TypedDict, Dict, List, Any


class RealEstateValuationState(TypedDict):
    """
    State that flows through the entire agent workflow
    All agents read from and write to this state
    """
    
    # User input
    user_query: str
    target_property: Dict[str, Any]
    
    # Agent 1 outputs
    query_analysis: Dict[str, Any]
    
    # Agent 2 outputs
    zip_discovery: Dict[str, Any]
    
    # Agent 3 outputs
    scraped_data: Dict[str, Any]
    
    # Agent 4 outputs
    preprocessed_data: Dict[str, Any]
    
    # Agent 5 outputs
    valuation_report: Dict[str, Any]
    
    # Metadata
    workflow_start_time: str
    workflow_end_time: str
    total_execution_time_seconds: float
    
    # Error handling
    errors: List[str]
    warnings: List[str]