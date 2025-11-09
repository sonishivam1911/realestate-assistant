from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


QUERY_ANALYSIS_PROMPT = """You are a real estate search strategist. Analyze the user's query and create a comprehensive search plan.

USER QUERY: "{user_query}"

YOUR TASKS:

1. EXTRACT LOCATION INFORMATION:
   - Primary location (ZIP code, address, or city)
   - Extract ZIP code if explicitly mentioned
   - Extract city and state if present
   - Determine location type (zip/address/city)

2. UNDERSTAND USER INTENT:
   - Property valuation? (wants to know what a property is worth)
   - Market analysis? (wants to know market trends in an area)
   - Comparison? (comparing multiple properties/areas)

3. GENERATE DUCKDUCKGO SEARCH QUERIES:
   Create 8-10 highly specific search queries to find nearby ZIP codes within the SAME STATE. These queries should:
   
   **Query Types to Generate:**
   
   A. DIRECT ZIP CODE SEARCHES (3-4 queries):
      - "ZIP codes near [primary_zip] [state]"
      - "neighboring ZIP codes [city] [state] within 6 miles"
      - "[primary_zip] adjacent ZIP codes same state"
      - "ZIP codes within 5-6 miles of [primary_zip] [state]"
   
   B. GEOGRAPHIC/COUNTY SEARCHES (2-3 queries):
      - "[city] [state] surrounding ZIP codes"
      - "[county] county [state] ZIP codes list"
      - "ZIP code map [city] [state] radius 6 miles"
   
   C. DATABASE/TOOL SEARCHES (2-3 queries):
      - "USPS ZIP code lookup [city] [state] nearby"
      - "ZIP code radius search [primary_zip] [state] 6 miles"
      - "ZIP code finder [city] [state] surrounding areas"

4. DETERMINE SEARCH RADIUS:
   - Default: 5-6 miles (to get comprehensive data within reasonable distance)
   - Focus on SAME STATE only
   - Adjust based on location type (urban: 5 miles, suburban/rural: 6 miles)

5. SET TIMEFRAME:
   - Default: 6 months for sold homes
   - Extract if user specifies ("last year", "past 3 months", etc.)

OUTPUT FORMAT (JSON ONLY):
{{
    "location": {{
        "type": "zip|address|city",
        "value": "extracted location",
        "zip": "primary ZIP if available",
        "city": "city name",
        "state": "state abbreviation"
    }},
    "intent": "property_valuation|market_analysis|comparison",
    "search_queries": [
        "specific search query 1",
        "specific search query 2",
        "specific search query 3",
        "specific search query 4",
        "specific search query 5",
        "specific search query 6",
        "specific search query 7",
        "specific search query 8"
    ],
    "search_radius_miles": 6,
    "timeframe_months": 6,
    "specific_requirements": [
        "list of what user wants to know"
    ],
    "confidence": 0.0-1.0
}}

EXAMPLES:

Example 1:
Input: "What's my home worth in 78701?"
Output:
{{
    "location": {{"type": "zip", "value": "78701", "zip": "78701", "city": "Austin", "state": "TX"}},
    "intent": "property_valuation",
    "search_queries": [
        "ZIP codes near 78701 Austin TX",
        "neighboring ZIP codes 78701 Texas within 6 miles",
        "Austin TX downtown ZIP codes surrounding",
        "78701 adjacent ZIP codes same state Texas",
        "Travis County Austin TX ZIP codes",
        "ZIP codes within 5-6 miles 78701 Texas",
        "USPS ZIP code lookup Austin TX downtown nearby",
        "Austin Texas ZIP code map central 6 mile radius"
    ],
    "search_radius_miles": 6,
    "timeframe_months": 6,
    "specific_requirements": ["property_valuation", "comparable_homes"],
    "confidence": 0.95
}}

Example 2:
Input: "Show me the Austin market trends"
Output:
{{
    "location": {{"type": "city", "value": "Austin TX", "city": "Austin", "state": "TX"}},
    "intent": "market_analysis",
    "search_queries": [
        "Austin Texas central ZIP codes list",
        "Austin TX surrounding ZIP codes within 6 miles",
        "Travis County ZIP codes Austin Texas",
        "Austin downtown Texas ZIP codes nearby",
        "ZIP code map Austin Texas 6 mile radius",
        "Austin TX metro area ZIP codes same state",
        "USPS Austin Texas ZIP codes surrounding",
        "Austin Texas ZIP code boundaries 6 miles"
    ],
    "search_radius_miles": 6,
    "timeframe_months": 6,
    "specific_requirements": ["market_trends", "price_trends", "inventory"],
    "confidence": 0.9
}}

Example 3:
Input: "Value 123 Main Street Austin TX 78701"
Output:
{{
    "location": {{"type": "address", "value": "123 Main Street Austin TX 78701", "zip": "78701", "city": "Austin", "state": "TX"}},
    "intent": "property_valuation",
    "search_queries": [
        "ZIP codes near 78701 Texas",
        "78701 neighboring ZIP codes Austin TX within 5 miles",
        "Austin TX 78701 surrounding areas same state",
        "ZIP codes within 5-6 miles 78701 Texas",
        "Travis County central ZIP codes Texas",
        "Austin downtown area ZIP codes Texas",
        "78702 78703 78704 78705 Austin Texas",
        "USPS ZIP code radius 78701 Texas 5 miles"
    ],
    "search_radius_miles": 5,
    "timeframe_months": 6,
    "specific_requirements": ["property_valuation", "comparable_sales", "market_trends"],
    "confidence": 1.0
}}

CRITICAL RULES:
1. Return ONLY valid JSON - no markdown, no explanation
2. Make search queries SPECIFIC with actual location details
3. Include the primary location in most queries
4. Vary query styles to maximize ZIP discovery
5. Don't make up ZIP codes - queries should help FIND them
6. Focus on findable, real data sources (USPS, county sites, ZIP databases)

NOW ANALYZE THIS QUERY:
"{user_query}"

Return ONLY the JSON output.
"""


def get_query_analysis_prompt_template() -> ChatPromptTemplate:
    """
    Get the query analysis prompt template
    
    Returns:
        ChatPromptTemplate: Template for query analysis
    """
    return ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(QUERY_ANALYSIS_PROMPT),
    ])