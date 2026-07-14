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
    for key in (
        "enrich_citations",
        "comp_citations",
        "market_citations",
        "macro_citations",
    ):
        cites.extend(state.get(key) or [])
    return cites


def _research_is_insufficient(state: CMAState) -> bool:
    if state.get("status") == "failed":
        return True
    research = state.get("comp_research") or {}
    sold = research.get("primary_comps") or research.get("comps") or []
    return len(sold) == 0


def synthesis_node(state: CMAState) -> dict:
    citations = _all_citations(state)

    if _research_is_insufficient(state):
        errors = state.get("errors") or []
        error_text = "; ".join(errors) if errors else "No usable comparable sales were found."
        report = {
            "executive_summary": (
                "Insufficient data to produce a reliable CMA. " + error_text
            ),
            "recommended_list_price": None,
            "price_range": {"low": None, "mid": None, "high": None},
            "verdict": "insufficient_data",
            "confidence": "low",
            "why_this_price": [],
            "comp_table": [],
            "adjustment_grid": [],
            "risks_and_caveats": [error_text],
            "markdown_report": (
                "## CMA — Insufficient Data\n\n"
                f"{error_text}\n\n"
                "Please re-run with complete subject details or a wider search window."
            ),
        }
        return {
            "cma_report": report,
            "all_citations": citations,
            "status": "complete",
            "assistant_message": report["markdown_report"],
        }

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
