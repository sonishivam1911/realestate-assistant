"""Macro context — inflation, mortgage rates, local economy."""

MACRO_CONTEXT_SYSTEM = """You are a macroeconomic researcher for real estate CMA reports.
Search official sources: BLS CPI, Freddie Mac PMMS, FRED, local economic data.
Return valid JSON only."""

MACRO_CONTEXT_USER = """Research macro and local economic context for:

{search_context}

Search for:
- Local metro CPI / inflation trend (last 12 months)
- Current 30-year mortgage rate (Freddie Mac)
- National inflation context (CPI YoY)
- Local property tax trends if available
- How rates and inflation affect buyer demand in this market

Return JSON:
{{
  "local_inflation": {{"trend": "", "rate_pct": null, "source_url": ""}},
  "mortgage_rate_30yr": {{"rate_pct": null, "as_of": "", "source_url": ""}},
  "national_cpi_yoy_pct": null,
  "buyer_impact": "how macro affects buyers here",
  "seller_impact": "how macro affects sellers here",
  "headwinds": ["..."],
  "tailwinds": ["..."],
  "summary": "macro paragraph for CMA",
  "sources": [{{"url": "", "title": ""}}]
}}"""
