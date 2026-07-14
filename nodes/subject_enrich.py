"""Subject enrich node — fill missing property facts via web search before comps."""

import json
import logging

from output_parser import ActionParser
from prompts.cma_subject_enrich import SUBJECT_ENRICH_SYSTEM, SUBJECT_ENRICH_USER
from services.comp_analysis import merge_subject_details, missing_subject_fields
from services.geocode import build_search_context
from services.openrouter_client import chat_with_web_search
from workflow.cma_state import CMAState

from nodes.config import MODEL_RESEARCH, PRIMARY_RADIUS_MILES

logger = logging.getLogger(__name__)
_parser = ActionParser(use_json_repair=True)


def subject_enrich_node(state: CMAState) -> dict:
    if state.get("status") == "failed":
        return {}

    subject = dict(state.get("target_property") or {})
    missing = missing_subject_fields(subject)

    # Always normalize known fields; skip web call when enrichment is unnecessary.
    if not missing:
        normalized = merge_subject_details(subject, {})
        geo = state.get("geo") or {}
        return {
            "target_property": normalized,
            "search_context": build_search_context(
                geo,
                normalized,
                primary_radius_miles=float(
                    state.get("primary_radius_miles") or PRIMARY_RADIUS_MILES
                ),
            ),
            "subject_enrichment": {
                "skipped": True,
                "reason": "subject already complete",
                "missing_fields": [],
            },
        }

    prompt = SUBJECT_ENRICH_USER.format(
        subject_json=json.dumps(subject, indent=2),
        address=subject.get("address") or state.get("user_message", ""),
        search_context=state.get("search_context", ""),
        missing_fields=", ".join(missing),
    )

    result = chat_with_web_search(
        model=MODEL_RESEARCH,
        system_prompt=SUBJECT_ENRICH_SYSTEM,
        user_prompt=prompt,
        temperature=0.1,
        max_tokens=2048,
    )
    parsed = _parser.safe_json_parse(result["content"]) or {}
    if not isinstance(parsed, dict):
        parsed = {}

    enriched = merge_subject_details(subject, parsed)
    geo = state.get("geo") or {}
    primary_radius = float(state.get("primary_radius_miles") or PRIMARY_RADIUS_MILES)
    search_context = build_search_context(
        geo,
        enriched,
        primary_radius_miles=primary_radius,
    )

    still_missing = missing_subject_fields(enriched)
    return {
        "target_property": enriched,
        "search_context": search_context,
        "subject_enrichment": {
            "skipped": False,
            "missing_fields_before": missing,
            "missing_fields_after": still_missing,
            "enrichment_confidence": parsed.get("enrichment_confidence"),
            "enrichment_notes": parsed.get("enrichment_notes"),
            "source_urls": parsed.get("source_urls") or [],
            "raw": parsed,
        },
        "enrich_citations": result.get("citations") or [],
    }
