"""Comp research node — web search for sold/pending/active comps, then score/bucket."""

import json
import logging

from output_parser import ActionParser
from prompts.cma_comp_research import COMP_RESEARCH_SYSTEM, COMP_RESEARCH_USER
from services.comp_analysis import analyze_comp_research
from services.openrouter_client import chat_with_web_search
from workflow.cma_state import CMAState

from nodes.config import MODEL_RESEARCH, PRIMARY_RADIUS_MILES

logger = logging.getLogger(__name__)
_parser = ActionParser(use_json_repair=True)


def comp_research_node(state: CMAState) -> dict:
    subject = state.get("target_property") or {}
    primary_radius = float(state.get("primary_radius_miles") or PRIMARY_RADIUS_MILES)
    outer_radius = float(state.get("radius_miles") or 5)
    timeframe_months = int(state.get("timeframe_months") or 3)

    prompt = COMP_RESEARCH_USER.format(
        search_context=state.get("search_context", ""),
        subject_json=json.dumps(subject, indent=2),
        primary_radius_miles=primary_radius,
        radius_miles=outer_radius,
        timeframe_months=timeframe_months,
    )

    result = chat_with_web_search(
        model=MODEL_RESEARCH,
        system_prompt=COMP_RESEARCH_SYSTEM,
        user_prompt=prompt,
        temperature=0.2,
        max_tokens=8192,
    )

    parsed = _parser.safe_json_parse(result["content"]) or {
        "sold_comps": [],
        "pending_comps": [],
        "active_comps": [],
        "comps": [],
        "summary": result["content"],
        "data_quality": "low",
    }
    if not isinstance(parsed, dict):
        parsed = {
            "sold_comps": [],
            "summary": str(parsed),
            "data_quality": "low",
        }

    analyzed = analyze_comp_research(
        subject,
        parsed,
        primary_radius_miles=primary_radius,
        timeframe_months=timeframe_months,
    )

    return {
        "comp_research": analyzed,
        "comp_citations": result["citations"],
    }
