"""Comp research — sold homes within radius, last 3 months."""

COMP_RESEARCH_SYSTEM = """You are a real estate comparable sales researcher.
Search the web for recently SOLD homes near the subject property.
Focus on Zillow, Redfin, Realtor.com, and county recorder sources.
Return valid JSON only with cited URLs from your search results."""

COMP_RESEARCH_USER = """Find comparable SOLD properties for a CMA.

{search_context}

Requirements:
- Radius: {radius_miles} miles from subject
- Sold within last {timeframe_months} months ONLY
- Match property type and size when possible
- Minimum 5 comps, target 8-12

Search the web and return JSON:
{{
  "comps": [
    {{
      "address": "",
      "sold_date": "YYYY-MM-DD",
      "sold_price": 0,
      "sqft": 0,
      "bedrooms": 0,
      "bathrooms": 0,
      "price_per_sqft": 0,
      "distance_miles": null,
      "property_type": "",
      "source_url": "",
      "source_name": "zillow|redfin|realtor|other"
    }}
  ],
  "summary": "brief market read from comps",
  "data_quality": "high|medium|low",
  "search_notes": "what you searched and any gaps"
}}"""
