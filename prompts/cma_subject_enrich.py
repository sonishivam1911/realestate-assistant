"""Subject property enrichment — fill missing facts before comps."""

SUBJECT_ENRICH_SYSTEM = """You enrich a subject real estate property using web search.
Pull listing facts from Zillow, Redfin, Realtor.com, Homes.com, MLS public pages, and tax records.
Prefer recent listing data. Return valid JSON only. Do not invent sqft or year_built — use null if unfound."""

SUBJECT_ENRICH_USER = """Enrich this subject property for a professional CMA.

Known details (do not overwrite with weaker guesses; only fill gaps):
{subject_json}

Search address: {address}
Location context:
{search_context}

Missing or incomplete fields to prioritize: {missing_fields}

Return JSON:
{{
  "sqft": null,
  "year_built": null,
  "architectural_style": "ranch|colonial|cape_cod|split_level|contemporary|tudor|victorian|craftsman|bungalow|townhouse|other|null",
  "property_type": "single_family|townhouse|condo|multi_family|other|null",
  "lot_sqft": null,
  "garage_spaces": null,
  "bedrooms": null,
  "bathrooms": null,
  "asking_price": null,
  "amenities": ["pool", "garage", "..."],
  "stories": null,
  "condition_notes": "",
  "listing_status": "active|pending|sold|unknown",
  "source_urls": [""],
  "enrichment_confidence": "high|medium|low",
  "enrichment_notes": "what was found vs still missing"
}}"""
