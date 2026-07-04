"""CMA synthesis — client-ready report from all research branches."""

SYNTHESIS_SYSTEM = """You are a senior real estate analyst writing a client-facing CMA report.
Be specific, cite comps by address, explain your price recommendation clearly.
Return valid JSON matching the schema exactly."""

SYNTHESIS_USER = """Write a Comparative Market Analysis report.

SUBJECT PROPERTY:
{subject_json}

COMPARABLE SALES RESEARCH:
{comps_json}

MARKET PULSE:
{market_json}

MACRO CONTEXT:
{macro_json}

ALL CITATIONS:
{citations_json}

Return JSON:
{{
  "executive_summary": "one paragraph for the client",
  "recommended_list_price": 0,
  "price_range": {{"low": 0, "mid": 0, "high": 0}},
  "verdict": "underpriced|fair|overpriced|insufficient_data",
  "confidence": "high|medium|low",
  "why_this_price": ["reason 1 with comp reference", "reason 2", "..."],
  "comp_table": [
    {{
      "address": "",
      "sold_price": 0,
      "sold_date": "",
      "sqft": 0,
      "price_per_sqft": 0,
      "adjusted_note": "",
      "source_url": ""
    }}
  ],
  "market_conditions": "supply/demand narrative",
  "macro_context": "inflation and rates narrative",
  "buyer_demand_assessment": "",
  "supply_assessment": "",
  "recommendation": "actionable advice for seller/buyer",
  "estimated_days_to_sell": null,
  "risks_and_caveats": ["..."],
  "markdown_report": "full formatted CMA report in markdown with ## headers"
}}"""
