from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate


EMAIL_REFLECTION_PROMPT = """You are a professional email quality reviewer. Evaluate this real estate valuation email for clarity, professionalism, and conciseness.

CURRENT EMAIL:
Subject: {current_subject}
Body:
{current_body}

YOUR TASK: Score out of 10 and improve ONLY if score < 8. Maximum 2 iterations allowed.

QUICK SCORING (out of 10):
- Is it under 10 lines? (3 points)
- No headers/markdown? (2 points)
- Professional tone? (2 points)
- Includes comparable property links? (2 points)
- Clear recommendation? (1 point)

OUTPUT EXACTLY THIS FORMAT:

SCORE: [X/10]

IF SCORE >= 8:
✅ Email is ready. No improvements needed.

IF SCORE < 8:
🔧 IMPROVED EMAIL:
Subject: [Better subject]
[Rewritten body - max 10 lines, plain text, no headers, include property links as [Name](URL)]

RULES FOR IMPROVEMENT:
- Remove all headers and section labels
- Remove confidence level mentions
- Make it plain paragraph text only
- Include top 3 comparable properties with links: [Address](URL)
- Keep under 10 lines
- Be direct and actionable
"""


def get_email_reflection_prompt_template() -> ChatPromptTemplate:
    """
    Get email reflection prompt template for quality assurance
    
    Returns:
        ChatPromptTemplate: Template for evaluating and improving emails
    """
    return ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(EMAIL_REFLECTION_PROMPT),
    ])
