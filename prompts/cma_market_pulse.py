"""Market pulse — supply, demand, inventory, DOM."""

MARKET_PULSE_SYSTEM = """You are a real estate market analyst researching supply and demand.
Search the web for current market conditions. Return valid JSON only."""

MARKET_PULSE_USER = """Analyze market supply and demand for:

{search_context}

Search for:
- Active listings count in {radius_miles}-mile radius
- Average days on market (DOM)
- Price reductions / list-to-sold ratio trends
- Months of supply estimate
- Buyer's vs seller's market indicators

Return JSON:
{{
  "active_listings_estimate": null,
  "avg_days_on_market": null,
  "months_of_supply": null,
  "market_type": "sellers|balanced|buyers",
  "inventory_trend": "rising|stable|falling",
  "demand_signals": ["..."],
  "supply_signals": ["..."],
  "summary": "2-3 sentence market pulse",
  "sources": [{{"url": "", "title": ""}}]
}}"""
