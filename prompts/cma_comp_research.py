"""Comp research — sold / pending / active with style preference + adjustments."""

COMP_RESEARCH_SYSTEM = """You are a real estate comparable-sales researcher for professional CMAs.
Search the web for SOLD, PENDING, and ACTIVE listings near the subject.
Focus on Zillow, Redfin, Realtor.com, Homes.com, and county/public records.
Never hard-filter to one architectural style only. Prefer same style first, then include
other styles as supporting comps with explicit dollar adjustments.
Return valid JSON only with cited URLs from search results. Do not invent sale prices."""

COMP_RESEARCH_USER = """Find comparable properties for a CMA using Homes.com / pro methodology.

{search_context}

Subject property JSON:
{subject_json}

Search rules:
- Primary proximity target: within {primary_radius_miles} miles
- Outer search radius: {radius_miles} miles (use for fallbacks if primary is thin)
- Sold within last {timeframe_months} months for sold comps
- Property type must match legal class when possible (single_family vs condo/townhouse)
- Architectural style: PREFER same style as subject for primary comps
- If same-style solds are scarce, INCLUDE other styles as supporting comps with adjustments
- Also gather ACTIVE competition and PENDING under-contract homes
- Target 8-12 sold comps, up to 6 active, up to 4 pending
- For each sold/pending/active home capture DOM when available
- Adjustments: adjust the COMP toward the subject (standard CMA direction)
  Examples: subject has pool & comp does not → positive adjustment on comp;
  comp has more finished sqft → negative adjustment on comp

Return JSON:
{{
  "sold_comps": [
    {{
      "address": "",
      "status": "sold",
      "sold_date": "YYYY-MM-DD",
      "sold_price": 0,
      "list_price": null,
      "days_on_market": null,
      "sqft": 0,
      "bedrooms": 0,
      "bathrooms": 0,
      "year_built": null,
      "architectural_style": "",
      "property_type": "single_family|townhouse|condo|multi_family|other",
      "lot_sqft": null,
      "garage_spaces": null,
      "amenities": [],
      "price_per_sqft": 0,
      "distance_miles": null,
      "adjustments": [
        {{
          "factor": "pool|sqft|baths|garage|condition|lot|style|other",
          "amount": 0,
          "direction": "subject_superior|comp_superior|neutral",
          "note": ""
        }}
      ],
      "adjusted_price": 0,
      "source_url": "",
      "source_name": "zillow|redfin|realtor|homes|other"
    }}
  ],
  "pending_comps": [],
  "active_comps": [],
  "summary": "brief market read from comps",
  "data_quality": "high|medium|low",
  "search_notes": "what you searched, style coverage, and gaps"
}}

Notes:
- pending_comps / active_comps use the same field shape; use list_price and omit sold_price when unknown
- Include a mix of styles in sold_comps when the neighborhood inventory is mixed; mark style clearly
- Prefer ranches for a ranch subject, colonials for a colonial subject, etc., but do not return only one style"""
