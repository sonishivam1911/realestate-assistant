from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


EMAIL_GENERATION_PROMPT = """You are a professional real estate valuation expert. Create a SHORT, PUNCHY email explaining property valuation in under 10 lines.

TARGET PROPERTY: {target_property_details}
VALUATION: {valuation_summary}
COMPARABLES: {comparable_properties}

STRICT REQUIREMENTS:
1. Max 10 lines total - be brutally concise
2. NO headers, NO sections, NO markdown formatting
3. NO confidence level mention (it's redundant)
4. NO repeated headers like "Market Analysis:" or "Recommendations:" 
5. Plain paragraph format only
6. Include property names as clickable links in body: [Property Address](URL)
7. Subject: Under 10 words, specific, professional

MUST INCLUDE (woven naturally into paragraphs):
- Estimated value vs asking price
- Why this valuation (1-2 lines max of explanation)
- List 3-5 top comparable properties with links
- Recommended action

MUST SKIP (too verbose):
- Confidence level / Medium/High labels
- Market trend discussions
- Property feature details
- Price per sqft explanations
- Lengthy recommendations

EXAMPLE FORMAT:

Subject: Quick Market Valuation - 123 Main St

Hi Sarah, your property at 123 Main St is valued at $450,000 compared to your asking price of $500,000. Based on 5 comparable sales in the area, the market supports a slightly lower price point. Key comparable sales: [Elm Street Property](URL1), [Oak Avenue Home](URL2), [Maple Drive Residence](URL3). We recommend pricing at $465,000 for a competitive edge. Call me to discuss next steps.

Best regards,
Real Estate Team

BE CONCISE. NO VERBOSITY. 10 LINES MAX.
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
