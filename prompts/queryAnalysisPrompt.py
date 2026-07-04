from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


QUERY_ANALYSIS_PROMPT = """You are a real estate search strategist. Analyze the user's query and create a comprehensive search plan.

USER QUERY: "{user_query}"

ANALYSIS TASKS:

1. EXTRACT LOCATION INFORMATION:
   - Primary location (ZIP code, address, or city)
   - City and state if present
   - Determine location type (zip/address/city)

2. UNDERSTAND USER INTENT:
   - property_valuation: User wants to know what a property is worth
   - market_analysis: User wants market trends in an area
   - comparison: Comparing multiple properties/areas

3. IDENTIFY ECONOMIC TIER OF PRIMARY LOCATION:
   Before searching for nearby ZIPs, identify the ECONOMIC STATUS/TIER of the primary location:
   
   TIER 1 - HIGH AFFLUENCE:
   - Keywords: "affluent", "wealthy", "upscale", "luxury", "premium", "exclusive", "executive", "estate", "high-end"
   - Characteristics: Median home values $1M+, gated communities, country clubs, prestigious addresses
   - Examples: Princeton NJ (08540), Atherton CA, Highland Park TX, Bel Air CA, Winnetka IL
   
   TIER 2 - MIDDLE/MODERATE:
   - Keywords: "suburban", "middle-class", "established", "family-friendly", "convenient"
   - Characteristics: Median home values $300K-$800K, mixed residential, accessible neighborhoods
   - Examples: Suburban areas around major cities
   
   TIER 3 - LOWER INCOME:
   - Keywords: "affordable", "budget", "working-class", "lower-income", "public housing", "industrial"
   - Characteristics: Median home values under $300K, rental-heavy, economically disadvantaged
   - Examples: Trenton NJ, Camden NJ, struggling urban centers
   
   CRITICAL RULE: ONLY search for ZIP codes with the SAME ECONOMIC TIER as primary location.
   Example: For primary "08540 Princeton NJ" (TIER 1 - wealthy), search ONLY for other TIER 1 affluent neighborhoods.
   Trenton NJ (TIER 3 - working-class) cannot be used, regardless of geographic proximity - DIFFERENT ECONOMIC TIER.

4. GENERATE SEARCH QUERIES (8-10 queries):
   Create DuckDuckGo queries to find ZIP codes within 4-5 MILES of the primary ZIP code.
   REQUIREMENTS: Same state + Same economic conditions as primary ZIP
   
   STEP 1: Determine economic tier of PRIMARY ZIP CODE provided by user
   STEP 2: Search for OTHER ZIP codes that are:
           - Within 4-5 miles radius of primary ZIP
           - In the SAME STATE
           - With MATCHING economic tier/conditions
   STEP 3: Return only ZIPs meeting ALL three criteria
   
   Query Examples for Different Economic Tiers:
   
   IF PRIMARY ZIP IS AFFLUENT (e.g., 08540 Princeton NJ - wealthy):
   - "ZIP codes within 5 miles of [primary_zip] [state] affluent"
   - "[state] affluent neighborhoods near [primary_zip]"
   - "ZIP codes surrounding [primary_zip] wealthy areas [state]"
   - "[primary_city] [state] wealthy ZIP codes nearby"
   - "[county] [state] high-value areas within 5 miles [primary_zip]"
   
   IF PRIMARY ZIP IS MODERATE/MIDDLE-CLASS:
   - "ZIP codes within 5 miles of [primary_zip] [state] middle-class"
   - "[state] suburban neighborhoods near [primary_zip]"
   - "ZIP codes surrounding [primary_zip] [state]"
   
   IF PRIMARY ZIP IS LOWER-INCOME/AFFORDABLE:
   - "ZIP codes within 5 miles of [primary_zip] [state] affordable"
   - "[state] budget neighborhoods near [primary_zip]"
   - "ZIP codes surrounding [primary_zip] [state]"
   
   CRITICAL: Search within 4-5 MILE RADIUS of primary ZIP only
   CRITICAL: MATCH ECONOMIC CONDITIONS - exclude different economic tiers
   CRITICAL: Same state only - NO cross-state results
   CRITICAL: If primary ZIP is affluent (e.g., Princeton 08540), exclude working-class areas (e.g., Trenton 08601)
   CRITICAL: Example: For 08540 Princeton NJ (wealthy), find affluent ZIPs within 5 miles in NJ only

5. DETERMINE SEARCH PARAMETERS:
   - Radius: 4-5 miles (fixed radius around primary ZIP code)
   - State: SAME STATE only
   - Economic Match: SAME ECONOMIC TIER as primary ZIP (mandatory)
   - Timeframe: 6 months for sold homes (default)
   - CRITICAL: Must meet ALL three criteria:
     1. Within 4-5 miles of primary ZIP
     2. Same state
     3. Same economic conditions/tier
   - CRITICAL: Do NOT prioritize geography over economic tier - both are REQUIRED, not optional

OUTPUT FORMAT (JSON only, no markdown):
{{
    "location": {{
        "type": "zip|address|city",
        "value": "extracted location string",
        "zip": "5-digit ZIP if available or null",
        "city": "city name or null",
        "state": "2-letter state code or null"
    }},
    "intent": "property_valuation|market_analysis|comparison",
    "search_queries": [
        "query 1",
        "query 2",
        "query 3",
        "query 4",
        "query 5",
        "query 6",
        "query 7",
        "query 8"
    ],
    "search_radius_miles": 6,
    "timeframe_months": 6,
    "specific_requirements": ["list", "of", "needs"],
    "confidence": 0.85
}}

CRITICAL RULES:
1. Return ONLY valid JSON - no markdown, no code blocks
2. Make queries SPECIFIC with actual location from user query
3. Always include STATE name in queries to filter results
4. SEARCH RADIUS: 4-5 miles from primary ZIP code (mandatory)
5. Include economic tier keywords that match primary ZIP in queries
6. Do NOT fabricate ZIP codes - queries help DISCOVER them
7. Vary query styles to maximize discovery of comparable ZIPs within 4-5 mile radius
8. CRITICAL: All comparables MUST meet THREE criteria:
   - Within 4-5 miles of primary ZIP
   - Same state
   - Same economic tier/conditions
9. CRITICAL: Economic tier MUST MATCH - geographic proximity alone is NOT sufficient
10. CRITICAL EXAMPLE: 08540 Princeton NJ (affluent) cannot use 08601 Trenton NJ (working-class),
    even though both are in NJ - they have different economic tiers. Must find affluent ZIPs within 5 miles of 08540.

NOW ANALYZE THE USER QUERY.
Return ONLY the JSON output.
"""


def get_query_analysis_prompt_template() -> ChatPromptTemplate:
    """Get query analysis prompt template"""
    return ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(QUERY_ANALYSIS_PROMPT),
    ])