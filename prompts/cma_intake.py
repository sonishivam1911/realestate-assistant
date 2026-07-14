"""CMA intake — parse address and property details from user message."""

INTAKE_SYSTEM = """You extract structured property and CMA request data from user messages.
Return valid JSON only. No markdown. Use null for unknown fields — never invent sqft or style."""

INTAKE_USER = """Parse this real estate CMA request:

"{user_message}"

Return JSON:
{{
  "address": "full street address",
  "city": "city or null",
  "state": "2-letter state or null",
  "zipcode": "5-digit zip or null",
  "radius_miles": 5,
  "property": {{
    "bedrooms": null,
    "bathrooms": null,
    "sqft": null,
    "year_built": null,
    "architectural_style": "ranch|colonial|cape_cod|split_level|contemporary|tudor|victorian|craftsman|bungalow|townhouse|other|null",
    "property_type": "single_family|townhouse|condo|multi_family|other",
    "lot_sqft": null,
    "garage_spaces": null,
    "amenities": [],
    "asking_price": null
  }},
  "intent": "cma|market_analysis|general",
  "timeframe_months": 3
}}

Default radius_miles to 5 if not specified. Default timeframe_months to 3 for sold comps.
Map features like pool / finished laundry / fireplace into amenities when mentioned.
garage_spaces: 2 for "2 car garage", etc."""
