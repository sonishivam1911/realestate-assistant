from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


ZIP_EXTRACTION_PROMPT = """You are a ZIP code extraction specialist for affluent neighborhoods.

PRIMARY ZIP: {primary_zip}
SEARCH RESULTS:
{search_results_text}

TASK: Extract max 2 valid ZIP codes that match these criteria:

MANDATORY FILTERS:
1. Geographic: Within 4-5 miles of {primary_zip}
2. Political: SAME STATE as {primary_zip}
3. Economic: SAME ECONOMIC TIER as {primary_zip}

ECONOMIC TIER MATCHING:
Identify the economic tier of primary ZIP first, then match ONLY with same tier:

TIER 1 - HIGH AFFLUENCE:
✓ KEEP: High-income, wealthy, upscale, luxury, premium, exclusive neighborhoods
Keywords: "affluent", "wealthy", "upscale", "luxury", "premium", "executive", "estate"

TIER 2 - MODERATE/MIDDLE-CLASS:
✓ KEEP: Suburban, family-friendly, established, convenient neighborhoods
Keywords: "suburban", "middle-class", "established", "family-friendly"

TIER 3 - LOWER INCOME:
✓ KEEP: Affordable, budget-friendly, working-class neighborhoods
Keywords: "affordable", "budget", "working-class", "lower-income", "public housing"

✗ EXCLUDE: ZIP codes from DIFFERENT economic tiers than primary ZIP
CRITICAL: Do NOT mix tiers - if primary is TIER 1 (wealthy), exclude TIER 2 and TIER 3 ZIPs

VALIDATION RULES:
- Must be exactly 5 digits (00501-99950 range)
- Must NOT be the primary ZIP {primary_zip}
- Must be mentioned in context of proximity/similarity to primary
- Must be in SAME STATE (strict - never cross state lines)
- Must be SAME ECONOMIC STATUS (strict - affluent only if primary is affluent)

SELECTION STRATEGY:
- Return MAX 2 ZIPs (quality over quantity)
- Prioritize the closest + most similar tier neighborhoods
- Return only the best matches that meet ALL criteria
- Focus on the BEST matches only

OUTPUT FORMAT:
Return ONLY a JSON array of max 2 ZIP code strings:
["12345", "23456"]

Do NOT return 3 ZIPs.

NOW EXTRACT ZIP CODES.
Return ONLY the JSON array with MAX 2 ZIPs matching ALL filters. No markdown, no explanation.
"""


def get_zip_extraction_prompt_template() -> ChatPromptTemplate:
    """Get ZIP extraction prompt template"""
    return ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(ZIP_EXTRACTION_PROMPT),
    ])