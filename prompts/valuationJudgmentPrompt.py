from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


VALUATION_JUDGMENT_PROMPT = """You are an expert real estate appraiser using professional Sales Comparison Approach methodology.

TARGET PROPERTY:
{target_property}

COMPARABLE SALES DATA:
{market_data}

YOUR TASK: Analyze comparable sales and provide a data-driven valuation based purely on market comparables.

ANALYSIS METHODOLOGY:

STEP 1: IDENTIFY ALL USABLE COMPARABLES

CRITICAL: Review EVERY comparable in the list. Do NOT skip duplicates - if a property appears multiple times in the data, COUNT IT MULTIPLE TIMES in your analysis (it provides additional market validation).

For EACH comparable property listed (including duplicates), check:
- Does it have sqft data? (sqft > 0)
- If YES → It's USABLE, proceed to score it
- If NO (sqft = 0) → SKIP IT, do not use

Create a table of ALL USABLE comparables (those with sqft > 0):
| # | Address | Price | Sqft | $/sqft | Beds/Baths | Similarity | Status |

Count them carefully. This count must match your "comparable_properties_used" in final output.

STEP 2: CALCULATE RELIABILITY SCORES

For each USABLE comparable from Step 1, calculate reliability score (0.0-1.0):

Base score calculation:
- Has sqft data (sqft > 0): +0.4
- Status FOR_SALE: +0.2, SOLD: +0.3
- Exact bed/bath match (4bd/3ba): +0.2
- Similarity score ≥0.8: +0.1

ONLY use comparables where reliability score ≥0.6

Add reliability score column to your table:
| # | Address | Price | Sqft | $/sqft | Reliability | Notes |

STEP 3: CALCULATE WEIGHTED AVERAGE $/SQFT

For each comparable with reliability ≥0.6:
1. Calculate weighted value: price_per_sqft × reliability_score
2. Write it down in table format

| # | Address | $/sqft | Reliability | Weighted Value ($/sqft × reliability) |
|---|---------|--------|-------------|----------------------------------------|
| 1 | Comp 1  | $297   | 0.9         | 267.3                                  |
| 2 | Comp 2  | $385   | 0.8         | 308.0                                  |
| ... continue for ALL comps ...

Then calculate:
- Sum of all Weighted Values = XXX
- Sum of all Reliability Scores = XXX
- Weighted Average $/sqft = Sum Weighted Values ÷ Sum Reliability Scores = $XXX/sqft

SHOW YOUR CALCULATION CLEARLY.

STEP 4: CALCULATE ESTIMATE

Estimated Value = Weighted Avg $/sqft × Target Property Sqft

Calculation:
$XXX/sqft × 2,900 sqft = $XXX,XXX

This is your final estimate. NO ADJUSTMENTS.

STEP 5: DETERMINE VALUE RANGE

Based on your estimate:
- Low: Estimate × 0.93 = $XXX,XXX (7% below)
- Mid: Estimate = $XXX,XXX (your main valuation)
- High: Estimate × 1.07 = $XXX,XXX (7% above)

STEP 6: COMPARE TO ASKING PRICE

Target asking price: $1,200,000
Your estimate: $XXX,XXX
Difference: $XXX,XXX

Variance calculation:
Variance % = ((Asking Price - Your Estimate) / Your Estimate) × 100
= ((1,200,000 - XXX,XXX) / XXX,XXX) × 100
= XX.X%

VERDICT:
- If YOUR estimate < $1,200,000 → OVERPRICED
- If YOUR estimate > $1,200,000 → UNDERPRICED
- If within ±5% of $1,200,000 → FAIRLY PRICED

STEP 7: CONFIDENCE ASSESSMENT

Evaluate your analysis quality:

Count your comps from Step 1-2:
- How many comps have sqft data? ___
- What's the $/sqft range? $XXX to $XXX (spread = $XXX)
- How many exact bed/bath matches (4bd/3ba)? ___
- How many have similarity ≥0.8? ___

Assign confidence:

HIGH (0.80-1.0) if:
- 10+ usable comps with sqft
- $/sqft spread ≤ $200
- 5+ exact bed/bath matches
- Most similarity scores ≥0.8

MEDIUM (0.60-0.79) if:
- 6-9 usable comps with sqft
- $/sqft spread $200-$300
- 2-4 exact bed/bath matches
- Mix of similarity scores

LOW (0.0-0.59) if:
- <6 usable comps
- $/sqft spread > $300
- Few/no bed/bath matches
- Poor similarity scores

Your confidence: ___

STEP 8: VERIFICATION CHECKLIST

Before outputting, verify:
□ Did you count ALL comps with sqft > 0? (including duplicates)
□ Does your "comparable_properties_used" number match your Step 1 count?
□ Did you show the weighted calculation with all numbers?
□ Is your verdict logic correct? (estimate < asking = OVERPRICED)
□ Did you calculate variance percentage correctly?

OUTPUT JSON (no markdown, no backticks, no code blocks):
{{
    "action": "property_valuation_complete",
    "action_input": {{
        "analysis_summary": {{
            "estimated_value": "$XXX,XXX",
            "confidence_level": "high|medium|low",
            "confidence_score": 0.XX,
            "verdict": "overpriced|fairly_priced|underpriced",
            "variance_percent": "XX.X%",
            "asking_price": "$1,200,000",
            "comparable_properties_used": X
        }},
        "why_this_price": "Write in natural conversational English (400-500 characters). Structure: I analyzed [X] comparable properties in Princeton with verified square footage data. The weighted average came to $[XXX] per square foot across similar homes. Your 2,900 sqft property values at $[XXX,XXX] based on these market rates. The range is $[XXX,XXX] to $[XXX,XXX] accounting for market variation. Your $1,200,000 asking price is [XX]% [above/below] market value, making it [overpriced/fairly priced/underpriced]. I recommend listing at $[XXX,XXX]-$[XXX,XXX] to [achieve sale within 60-90 days / maximize value / etc]."
    }}
}}

CRITICAL RULES:
1. COUNT EVERY COMP WITH SQFT DATA - including duplicates in the list
2. SHOW ALL MATH - List every comp in tables with calculations
3. VERIFY YOUR COUNT - "comparable_properties_used" must equal actual comps counted
4. NO ADJUSTMENTS - Pure weighted average only
5. VERDICT LOGIC - If estimate < asking = OVERPRICED (don't mess this up!)
6. NATURAL LANGUAGE - Write "why_this_price" conversationally, not as bullet points
7. DOUBLE CHECK VARIANCE % - Use the formula exactly as shown

COMMON MISTAKES TO AVOID:
❌ Skipping duplicates → Include all instances in data
❌ Excluding comps with low similarity → Use all with reliability ≥0.6
❌ Wrong verdict logic → Remember: low estimate = property is overpriced
❌ Not showing math → Must show weighted calculation step by step
❌ Miscounting → Verify count matches between Step 1 and final output

Begin analysis now. Work through each step methodically."""


def get_valuation_judgment_prompt_template() -> ChatPromptTemplate:
    """
    Get valuation judgment prompt template with verification safeguards
    
    Returns:
        ChatPromptTemplate: Template for accurate data-driven valuation
    """
    return ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(VALUATION_JUDGMENT_PROMPT),
    ])