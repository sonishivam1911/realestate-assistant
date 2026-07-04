"""Synthesis node — merge fan-out results into client CMA report."""

import json

from output_parser import ActionParser
from prompts.cma_synthesis import SYNTHESIS_SYSTEM, SYNTHESIS_USER
from services.openrouter_client import chat_completion
from workflow.cma_state import CMAState

from nodes.config import MODEL_SYNTHESIS

_parser = ActionParser(use_json_repair=True)


def _all_citations(state: CMAState) -> list:
    cites = []
    for key in ("comp_citations", "market_citations", "macro_citations"):
        cites.extend(state.get(key) or [])
    return cites


def synthesis_node(state: CMAState) -> dict:
    citations = _all_citations(state)
    prompt = SYNTHESIS_USER.format(
        subject_json=json.dumps(state.get("target_property", {}), indent=2),
        comps_json=json.dumps(state.get("comp_research", {}), indent=2),
        market_json=json.dumps(state.get("market_pulse", {}), indent=2),
        macro_json=json.dumps(state.get("macro_context", {}), indent=2),
        citations_json=json.dumps(citations, indent=2),
    )

    raw = chat_completion(
        model=MODEL_SYNTHESIS,
        system_prompt=SYNTHESIS_SYSTEM,
        user_prompt=prompt,
        temperature=0.3,
        max_tokens=8192,
        json_mode=True,
    )

    report = _parser.safe_json_parse(raw) or {
        "executive_summary": raw,
        "markdown_report": raw,
    }

    return {
        "cma_report": report,
        "all_citations": citations,
        "status": "complete",
        "assistant_message": report.get("markdown_report") or report.get("executive_summary", ""),
    }
