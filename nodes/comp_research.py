"""Comp research node — web search for sold comps (fan-out branch)."""

import logging

from output_parser import ActionParser
from prompts.cma_comp_research import COMP_RESEARCH_SYSTEM, COMP_RESEARCH_USER
from services.openrouter_client import chat_with_web_search
from workflow.cma_state import CMAState

from nodes.config import MODEL_RESEARCH

logger = logging.getLogger(__name__)
_parser = ActionParser(use_json_repair=True)


def comp_research_node(state: CMAState) -> dict:
    prompt = COMP_RESEARCH_USER.format(
        search_context=state["search_context"],
        radius_miles=state.get("radius_miles", 5),
        timeframe_months=state.get("timeframe_months", 3),
    )

    result = chat_with_web_search(
        model=MODEL_RESEARCH,
        system_prompt=COMP_RESEARCH_SYSTEM,
        user_prompt=prompt,
        temperature=0.2,
        max_tokens=4096,
    )

    parsed = _parser.safe_json_parse(result["content"]) or {
        "comps": [],
        "summary": result["content"],
        "data_quality": "low",
    }

    return {
        "comp_research": parsed,
        "comp_citations": result["citations"],
    }
