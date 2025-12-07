from typing import TypedDict, Dict, List, Any


class RealEstateValuationState(TypedDict):
    """
    State that flows through the entire agent workflow
    All agents read from and write to this state
    """
    
    # User input
    user_query: str
    target_property: Dict[str, Any]
    
    # Filter parameters for scraping
    filters: Dict[str, Any]  # bedrooms, bathrooms, property_type, min_sqft, max_sqft, year_built, etc.
    
    # Agent 1 outputs
    query_analysis: Dict[str, Any]
    
    # Agent 2 outputs
    zip_discovery: Dict[str, Any]
    
    # Agent 3 outputs
    scraped_data: Dict[str, Any]
    
    # Agent 4 outputs
    preprocessed_data: Dict[str, Any]
    
    # User Selection - Interrupt Point
    selected_properties: List[Dict[str, Any]]  # Properties user selected from displayed cards
    
    # Agent 5 outputs
    valuation_report: Dict[str, Any]
    
    # Agent 6 & 7 outputs (Email Generation & Reflection)
    email_data: Dict[str, Any]
    email_recipient_name: str
    email_reflection_result: Dict[str, Any]
    
    # Metadata
    workflow_start_time: str
    workflow_end_time: str
    total_execution_time_seconds: float
    
    # Error handling
    errors: List[str]
    warnings: List[str]
    
    # Workflow control
    interrupt_flag: bool  # Flag to pause workflow for user interaction
    available_properties: List[Dict[str, Any]]  # Properties available for selection