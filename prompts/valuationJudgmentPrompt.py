from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


VALUATION_JUDGMENT_PROMPT = """You are an expert real estate appraiser using professional Sales Comparison Approach methodology.

TARGET PROPERTY:
{target_property}

TARGET PROPERTY SQUARE FOOTAGE:
{target_sqft} sqft

ASKING PRICE:
{asking_price}

COMPARABLE SALES DATA:
{market_data}

YOUR TASK: Analyze comparable sales and provide a data-driven valuation based purely on market comparables.

⚠️ CRITICAL REQUIREMENTS FOR THIS ANALYSIS:

1️⃣  ALL COMPARABLES MUST HAVE SQUARE FOOTAGE DATA
   - Do NOT use properties without sqft data
   - Square footage is ESSENTIAL for price-per-sqft calculations
   - If a property has sqft = 0 or missing → REJECT IT immediately

2️⃣  EXACT BEDROOM & BATHROOM MATCHES ONLY
   - All comparables in this list already match the target property's bed/bath count exactly
   - If you notice any mismatches, do NOT use those properties
   
3️⃣  SIMILAR SQUARE FOOTAGE (±15% tolerance)
   - Properties should be within 15% of target property sqft
   - Large sqft differences (>15%) should receive lower reliability scores
   - Penalize significantly different sqft values in your calculations

ANALYSIS METHODOLOGY:

STEP 1: IDENTIFY ALL USABLE COMPARABLES

CRITICAL: Review EVERY comparable in the list. Do NOT skip duplicates - if a property appears multiple times in the data, COUNT IT MULTIPLE TIMES in your analysis (it provides additional market validation).

For EACH comparable property listed (including duplicates), check:
- Does it have sqft data? (sqft > 0) → REQUIRED!
- If YES → It's USABLE, proceed to score it
- If NO (sqft = 0) → SKIP IT, do not use (this should not happen, but verify)

Create a table of ALL USABLE comparables (those with sqft > 0):
| # | Address | Price | Sqft | $/sqft | Beds/Baths | Similarity | Status |

Count them carefully. This count must match your "comparable_properties_used" in final output.

STEP 2: CALCULATE RELIABILITY SCORES

For each USABLE comparable from Step 1, calculate reliability score (0.0-1.0):

Base score calculation:
- Has sqft data (sqft > 0): +0.4 (REQUIRED - if missing, score is 0)
- Status FOR_SALE: +0.2, SOLD: +0.3
- Exact bed/bath match: +0.2 (MUST be exact, already verified)
- Similar sqft (within ±15% of target): +0.1 bonus (penalize if >15% different)
- Similarity score ≥0.8: +0.1

Add reliability score column to your table:
| # | Address | Price | Sqft | $/sqft | Reliability | Notes |

STEP 2.5: VERIFY QUALIFYING COMPARABLES (CRITICAL STEP!)

Before proceeding to calculations, explicitly list EVERY comp with reliability ≥0.6:

QUALIFYING COMPS FOR VALUATION (reliability ≥0.6):
1. [Address] - $/sqft: $XXX - Reliability: 0.X ✓
2. [Address] - $/sqft: $XXX - Reliability: 0.X ✓
3. [Address] - $/sqft: $XXX - Reliability: 0.X ✓
... (continue for ALL comps with reliability ≥0.6)

TOTAL QUALIFYING COMPS: ___ comps

CRITICAL VERIFICATION:
□ Did I list EVERY comp from Step 2 with reliability ≥0.6?
□ This count MUST match the number of rows in my Step 3 calculation table
□ If I listed 4 comps here, Step 3 must have 4 rows of calculations

STEP 3: CALCULATE WEIGHTED AVERAGE $/SQFT

For EACH qualifying comparable from Step 2.5 (ALL comps with reliability ≥0.6):

Create weighted calculation table with ONE ROW per qualifying comp:
| # | Address | $/sqft | Reliability | Weighted Value ($/sqft × reliability) |
|---|---------|--------|-------------|----------------------------------------|
| 1 | [Comp 1 from Step 2.5] | $XXX | 0.X | XXX.XX |
| 2 | [Comp 2 from Step 2.5] | $XXX | 0.X | XXX.XX |
| 3 | [Comp 3 from Step 2.5] | $XXX | 0.X | XXX.XX |
... (continue for ALL comps from Step 2.5)

VERIFICATION: Number of rows in this table = ___ (must match Step 2.5 count!)

Then calculate:
Step A: Sum of all Weighted Values = XXX.XX + XXX.XX + XXX.XX + ... = TOTAL
Step B: Sum of all Reliability Scores = 0.X + 0.X + 0.X + ... = TOTAL
Step C: Division: TOTAL from Step A ÷ TOTAL from Step B = $XXX/sqft

Weighted Average $/sqft = $XXX/sqft

SANITY CHECK:
□ Is my weighted avg $/sqft between $200-$600? (normal for residential)
□ If NO: I made a calculation error - recalculate!
□ If YES: Proceed to Step 4

STEP 4: CALCULATE ESTIMATE

Estimated Value = Weighted Avg $/sqft × Target Property Sqft

Target Property Details:
- Square Footage: {target_sqft} sqft
- Bedrooms: {target_beds}
- Bathrooms: {target_baths}

Calculation:
$XXX/sqft × {target_sqft} sqft = $XXX,XXX

This is your final estimate. NO ADJUSTMENTS.

STEP 5: DETERMINE VALUE RANGE

Based on your estimate:
- Low: Estimate × 0.93 = $XXX,XXX (7% below)
- Mid: Estimate = $XXX,XXX (your main valuation)
- High: Estimate × 1.07 = $XXX,XXX (7% above)

STEP 6: COMPARE TO ASKING PRICE

Target asking price: {asking_price}
Your estimate: $XXX,XXX
Difference: $XXX,XXX

Variance calculation:
Variance % = ((Your Estimate - Asking Price) / Asking Price) × 100
= ((XXX,XXX - {asking_price_numeric}) / {asking_price_numeric}) × 100
= XX.X%

VERDICT:
- If YOUR estimate > {asking_price} → UNDERPRICED (asking price is too low - good deal for buyer!)
- If YOUR estimate < {asking_price} → OVERPRICED (asking price is too high)
- If within ±5% of {asking_price} → FAIRLY PRICED

STEP 7: CONFIDENCE ASSESSMENT

Evaluate your analysis quality:

Target Property Context:
- Square Footage: {target_sqft} sqft
- Bedrooms: {target_beds}
- Bathrooms: {target_baths}

Count your comps from Step 1-2.5:
- How many comps have sqft data? ___ (from Step 1)
- How many qualify with reliability ≥0.6? ___ (from Step 2.5)
- What's the $/sqft range? $XXX to $XXX (spread = $XXX)
- How many exact bed/bath matches ({target_beds}bd/{target_baths}ba)? ___
- How many have similarity ≥0.8? ___
- How do target sqft ({target_sqft} sqft) compare to comps? ___ (within 15%? larger? smaller?)

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

STEP 8: FINAL VERIFICATION CHECKLIST

Before outputting JSON, verify these numbers match:

✓ Step 1 count (comps with sqft) = ___ 
✓ Step 2.5 count (reliability ≥0.6) = ___
✓ Step 3 table rows = ___ (must match Step 2.5!)
✓ "comparable_properties_used" in output = ___ (use Step 2.5 count)

CRITICAL: Step 2.5 count, Step 3 rows, and output count MUST ALL BE THE SAME NUMBER!

Additional checks:
□ Did you count ALL comps with sqft > 0? (including duplicates)
□ Did you include ALL comps with reliability ≥0.6 in Step 3?
□ Did you show the weighted calculation with all numbers?
□ Is your verdict logic correct? (estimate > asking = UNDERPRICED, estimate < asking = OVERPRICED)
□ Did you calculate variance percentage correctly?
□ Is your weighted avg $/sqft reasonable ($200-$600)?

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
            "asking_price": "{asking_price}",
            "comparable_properties_used": X
        }},
        "why_this_price": "Write in natural conversational English (400-500 characters). Structure: I analyzed [X] comparable properties in [LOCATION] with verified square footage data. The weighted average came to $[XXX] per square foot across similar homes. Your [SQFT] sqft property values at $[XXX,XXX] based on these market rates. The range is $[XXX,XXX] to $[XXX,XXX] accounting for market variation. Your {asking_price} asking price is [XX]% [above/below] market value, making it [overpriced/fairly priced/underpriced]. I recommend listing at $[XXX,XXX]-$[XXX,XXX] to [achieve sale within 60-90 days / maximize value / etc]."
    }}
}}

CRITICAL RULES:
1. COUNT EVERY COMP WITH SQFT DATA - including duplicates in the list
2. SHOW ALL MATH - List every comp in tables with calculations
3. USE STEP 2.5 VERIFICATION - List all qualifying comps before calculating
4. STEP 3 MUST INCLUDE ALL COMPS FROM STEP 2.5 - Don't skip any!
5. VERIFY YOUR COUNT - Three places must match: Step 2.5, Step 3 rows, final output
6. NO ADJUSTMENTS - Pure weighted average only
7. VERDICT LOGIC - If estimate > asking = UNDERPRICED (good deal!), if estimate < asking = OVERPRICED
8. NATURAL LANGUAGE - Write "why_this_price" conversationally, not as bullet points
9. DOUBLE CHECK VARIANCE % - Use the formula exactly as shown
10. SANITY CHECK YOUR $/SQFT - Should be $200-$600 for residential

COMMON MISTAKES TO AVOID:
❌ Skipping duplicates → Include all instances in data
❌ Excluding comps with reliability ≥0.6 from Step 3 → Use ALL qualifying comps
❌ Step 2.5 count ≠ Step 3 rows → They MUST match
❌ Wrong verdict logic → Remember: high estimate means property asking price is too low (underpriced/good deal), low estimate means asking price is too high (overpriced)
❌ Not showing math → Must show weighted calculation step by step
❌ Unreasonable $/sqft → If outside $200-$600, you made an error

Begin analysis now. Work through each step methodically and use the verification checkpoints."""


def get_valuation_judgment_prompt_template() -> ChatPromptTemplate:
    """
    Get valuation judgment prompt template with mandatory verification steps
    
    Returns:
        ChatPromptTemplate: Template for accurate data-driven valuation
    """
    return ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(VALUATION_JUDGMENT_PROMPT),
    ])