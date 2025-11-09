from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


VALUATION_JUDGMENT_PROMPT = """You are a senior real estate appraiser with 20+ years of experience. Make a professional valuation judgment based on the provided market data.

TARGET PROPERTY:
{target_property}

MARKET DATA (Preprocessed & Cleaned):
{market_data}

YOUR TASK:
Analyze the market data and make a comprehensive valuation judgment. Use the comparable sales to estimate the property value.

VALUATION METHODOLOGY:
1. Review the top comparables (already ranked by similarity)
2. Calculate weighted average price per sqft from top 10 comps
3. Apply adjustments for property differences
4. Consider market trend (hot/cooling/stable)
5. Factor in data quality and confidence
6. Generate price range (low/mid/high estimates)

CRITICAL ANALYSIS POINTS:
- Are the comparables truly comparable? (size, beds, location)
- How recent are the sales? (recent = more weight)
- What's the market trend? (adjust up if hot, down if cooling)
- Is data quality high enough for confident valuation?
- Any outliers that should be excluded?

OUTPUT FORMAT (JSON ONLY):
{{
    "estimated_value": {{
        "low": 450000,
        "mid": 475000,
        "high": 500000,
        "recommended_listing_price": 479000,
        "calculation_method": "weighted_average_price_per_sqft"
    }},
    "price_per_sqft_analysis": {{
        "comparable_avg_ppsf": 265,
        "target_estimated_ppsf": 264,
        "calculation": "264 * 1800 sqft = $475,200"
    }},
    "comparable_analysis": {{
        "total_comps_used": 10,
        "comps_summary": [
            {{
                "address": "123 Main St",
                "price": 450000,
                "sqft": 1750,
                "ppsf": 257,
                "weight": 0.15,
                "reasoning": "Very similar size and recent sale"
            }}
        ],
        "best_comparable": {{
            "address": "...",
            "reason": "Most similar property"
        }}
    }},
    "market_analysis": {{
        "trend": "hot|stable|cooling",
        "inventory_status": "low|balanced|high",
        "days_on_market_avg": 45,
        "price_trend_6mo": "+5.2%",
        "market_adjustment": "+3% for hot market"
    }},
    "confidence": {{
        "overall_confidence": "high|medium|low",
        "score": 0.85,
        "factors": [
            "30+ quality comparables",
            "Recent sales (last 3 months)",
            "High similarity scores",
            "Stable market conditions"
        ],
        "concerns": [
            "Limited data for luxury segment",
            "Seasonal pricing variations"
        ]
    }},
    "reasoning": {{
        "valuation_logic": "Used weighted average of top 10 comparables...",
        "key_adjustments": [
            "+$10K for better location",
            "-$5K for older property"
        ],
        "market_context": "Hot market with low inventory...",
        "final_judgment": "Property is fairly priced at asking..."
    }},
    "recommendations": {{
        "for_sellers": [
            "List at $479,000 for quick sale",
            "Expect 30-45 days on market",
            "Highlight recent renovations"
        ],
        "for_buyers": [
            "Fair market value confirmed",
            "Offer $470K-$475K range",
            "Property is competitive at asking"
        ],
        "pricing_strategy": "Competitive pricing in hot market"
    }}
}}

EXAMPLE CALCULATION:
If top 10 comparables have price per sqft of [250, 260, 255, 265, 258, 262, 254, 261, 257, 259]:
- Average: 258 per sqft
- Target property: 1800 sqft
- Base estimate: 258 * 1800 = $464,400
- Hot market adjustment: +3% = $478,332
- Final estimate: $478,000 (rounded)

CRITICAL RULES:
1. Return ONLY valid JSON - no markdown, no explanation outside JSON
2. Base valuation on ACTUAL comparable data provided
3. Show your math in the calculation field
4. Be honest about confidence level
5. Provide actionable recommendations
6. Consider market trend in final estimate

NOW GENERATE THE VALUATION REPORT.
Return ONLY the JSON output.
"""


def get_valuation_judgment_prompt_template() -> ChatPromptTemplate:
    """
    Get valuation judgment prompt template
    
    Returns:
        ChatPromptTemplate: Template for valuation judgment
    """
    return ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(VALUATION_JUDGMENT_PROMPT),
    ])