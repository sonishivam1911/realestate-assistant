from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


EMAIL_GENERATION_PROMPT = """You are a professional real estate valuation expert. Create a concise, professional email explaining property valuation in 2-3 short paragraphs.

TARGET PROPERTY: {target_property_details}
VALUATION: {valuation_summary}
COMPARABLES: {comparable_properties}

STRICT REQUIREMENTS:
1. 2-3 short paragraphs (15-20 lines total max)
2. NO headers, NO sections, NO bullet points, NO markdown formatting
3. Plain paragraph format only - natural flowing prose
4. Professional but friendly tone
5. Subject line: Under 10 words, specific, professional

PARAGRAPH 1 - EXECUTIVE SUMMARY (3-5 lines):
- Open with greeting using recipient name
- State estimated value vs asking price with clear numbers (format: $XXX,XXX)
- State verdict clearly (overpriced/underpriced/fairly priced)
- Brief 1-2 sentence explanation of WHY this valuation (key factors driving the number)

PARAGRAPH 2 - COMPARABLE PROPERTIES (5-8 lines):
- Introduce the comparable properties used for analysis
- List 3-5 top comparable properties as clickable links with prices
- Format EXACTLY as: [Full Property Address](zillow_url) at $XXX,XXX
- CRITICAL: Use the actual Zillow URLs from comparable_properties data
- CRITICAL: Format prices correctly with commas (e.g., $450,000 not 450000)
- Keep this section flowing naturally, not as a list

PARAGRAPH 3 - RECOMMENDATION & NEXT STEPS (3-5 lines):
- Clear pricing recommendation (specific dollar amount)
- Suggested next steps (e.g., "schedule a call to discuss", "adjust listing price", etc.)
- Warm closing encouraging action

FORMATTING RULES:
- All prices MUST be formatted as: $XXX,XXX (with dollar sign and commas)
- Property links MUST be: [Full Address](URL) - use actual URLs from data
- NO broken formatting like "295730whichis" - always add commas and spaces
- NO placeholder text like "__Property Name__" - use actual clickable markdown links
- Ensure proper spacing between words and numbers

SKIP ENTIRELY:
- Confidence level mentions (Medium/High/Low)
- Market trend discussions
- Property feature comparisons (beds/baths/sqft details)
- Price per sqft breakdowns
- Verbose explanations

EXAMPLE OUTPUT:

Subject: Market Valuation - 262 Kempsey Dr

Hi Sarah,

Your property at 262 Kempsey Dr, North Brunswick, NJ is valued at $295,730, which is $51,270 lower than your asking price of $347,000, indicating the property is currently overpriced. This valuation is based on recent comparable sales in your area showing similar properties selling at lower price points, particularly townhomes built in the 1980s with similar square footage.

Based on our analysis of the local market, we reviewed several comparable properties: [63 Pennsylvania Way, North Brunswick](https://www.zillow.com/...) at $285,000, [318 Wimbledon Ct, North Brunswick](https://www.zillow.com/...) at $305,000, [1224 Dogwood Ct, North Brunswick](https://www.zillow.com/...) at $290,000, and [156 Tamarack Way, North Brunswick](https://www.zillow.com/...) at $298,500. These properties share similar characteristics with yours and have recently sold or are listed in your neighborhood.

We recommend adjusting your listing price to $310,000 to attract more buyers and remain competitive. I'd be happy to schedule a call this week to discuss pricing strategy and next steps for your listing. Please let me know what works best for your schedule.

Best regards,
Real Estate Team

CRITICAL REMINDERS:
- Format ALL prices with $ and commas: $347,000 NOT 347000
- Use REAL Zillow URLs from the comparable_properties data
- Keep it to 2-3 paragraphs, NO MORE
- NO headers, NO sections, just flowing paragraphs
- Be concise but informative
"""


def get_email_generation_prompt_template() -> ChatPromptTemplate:
    """
    Get email generation prompt template
    
    Returns:
        ChatPromptTemplate: Template for generating professional client emails
    """
    return ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(EMAIL_GENERATION_PROMPT),
    ])