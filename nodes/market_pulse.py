"""Market pulse node — supply/demand (fan-out branch)."""

from output_parser import ActionParser
from prompts.cma_market_pulse import MARKET_PULSE_SYSTEM, MARKET_PULSE_USER
from services.openrouter_client import chat_with_web_search
from workflow.cma_state import CMAState

from nodes.config import MODEL_RESEARCH

_parser = ActionParser(use_json_repair=True)


def market_pulse_node(state: CMAState) -> dict:
    prompt = MARKET_PULSE_USER.format(
        search_context=state["search_context"],
        radius_miles=state.get("radius_miles", 5),
    )

    result = chat_with_web_search(
        model=MODEL_RESEARCH,
        system_prompt=MARKET_PULSE_SYSTEM,
        user_prompt=prompt,
        temperature=0.2,
        max_tokens=3072,
    )

    parsed = _parser.safe_json_parse(result["content"]) or {
        "summary": result["content"],
        "market_type": "unknown",
    }

    return {
        "market_pulse": parsed,
        "market_citations": result["citations"],
    }
