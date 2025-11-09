from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


ZIP_EXTRACTION_PROMPT = """You are a ZIP code extraction specialist. Extract ALL valid ZIP codes from search results.

PRIMARY ZIP CODE: {primary_zip}

SEARCH RESULTS:
{search_results_text}

YOUR TASK:
Extract ALL 5-digit ZIP codes that are NEAR or NEIGHBORING the primary ZIP code {primary_zip}.

EXTRACTION RULES:

1. LOOK FOR:
   - ZIP codes explicitly mentioned as "near {primary_zip}"
   - ZIP codes in the same city/county
   - ZIP codes mentioned in lists of neighboring areas
   - ZIP codes on maps or geographic descriptions
   - ZIP codes in USPS databases or tools

2. VALID ZIP CODES:
   - Must be exactly 5 digits
   - Must be in range 00501-99950
   - Must be geographically related to {primary_zip}

3. EXCLUDE:
   - The primary ZIP ({primary_zip}) itself
   - ZIP codes from obviously different states/regions
   - Phone numbers or other 5-digit numbers
   - ZIP codes mentioned as examples unrelated to the search area

4. CONFIDENCE:
   - HIGH confidence: ZIP explicitly listed as neighboring/nearby
   - MEDIUM confidence: ZIP in same city/county
   - LOW confidence: ZIP mentioned but relationship unclear
   - Only include HIGH and MEDIUM confidence ZIPs

OUTPUT FORMAT:
Return ONLY a JSON array of ZIP codes (as strings):
["12345", "12346", "12347", "12348", ...]

EXAMPLES:

Search Result: "ZIP codes near 78701 include 78702, 78703, 78704, and 78705"
Output: ["78702", "78703", "78704", "78705"]

Search Result: "Austin downtown area ZIP codes: 78701 (primary), 78702 (east), 78703 (west)"
Output: ["78702", "78703"]

Search Result: "Travis County ZIP codes include 78701, 78702, 78703, 78731, 78746"
Output: ["78702", "78703", "78731", "78746"]

NOW EXTRACT ZIP CODES FROM THE SEARCH RESULTS ABOVE.

Return ONLY the JSON array. No explanation, no markdown, just the array.
"""


def get_zip_extraction_prompt_template() -> ChatPromptTemplate:
    """
    Get ZIP extraction prompt template
    
    Returns:
        ChatPromptTemplate: Template for ZIP extraction
    """
    return ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(ZIP_EXTRACTION_PROMPT),
    ])