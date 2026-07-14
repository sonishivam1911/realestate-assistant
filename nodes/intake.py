"""Intake node — parse user message, geocode address."""

import json
import logging
import os

from output_parser import ActionParser
from prompts.cma_intake import INTAKE_SYSTEM, INTAKE_USER
from services.geocode import build_search_context, geocode_address
from services.openrouter_client import chat_completion
from workflow.cma_state import CMAState

from nodes.config import DEFAULT_RADIUS_MILES, PRIMARY_RADIUS_MILES, TIMEFRAME_MONTHS

logger = logging.getLogger(__name__)
_parser = ActionParser(use_json_repair=True)


def _full_address_for_geocode(parsed: dict, fallback: str) -> str:
    """Build a complete address so geocoding does not match the wrong city."""
    street = (parsed.get("address") or "").strip()
    city = (parsed.get("city") or "").strip()
    state = (parsed.get("state") or "").strip()
    zipcode = (parsed.get("zipcode") or "").strip()
    parts = [part for part in (street, city, state, zipcode) if part]
    if len(parts) >= 2:
        return ", ".join(parts)
    return street or fallback


def intake_node(state: CMAState) -> dict:
    user_message = state["user_message"]
    model = os.getenv("CMA_MODEL_INTAKE", "deepseek/deepseek-v4-flash")

    raw = chat_completion(
        model=model,
        system_prompt=INTAKE_SYSTEM,
        user_prompt=INTAKE_USER.format(user_message=user_message),
        temperature=0.1,
        max_tokens=1024,
        json_mode=True,
    )
    parsed = _parser.safe_json_parse(raw) or {}

    address = parsed.get("address") or user_message
    geocode_query = _full_address_for_geocode(parsed, user_message)
    radius = float(parsed.get("radius_miles") or state.get("radius_miles") or DEFAULT_RADIUS_MILES)
    timeframe = int(parsed.get("timeframe_months") or TIMEFRAME_MONTHS)
    property_details = parsed.get("property") or state.get("target_property") or {}

    geo = geocode_address(geocode_query)
    if geo.get("error"):
        return {
            "errors": state.get("errors", []) + [geo["error"]],
            "status": "failed",
        }

    geo["radius_miles"] = radius
    primary_radius = min(PRIMARY_RADIUS_MILES, radius)
    # Prefer caller-supplied target_property fields over sparse LLM parse.
    provided = state.get("target_property") or {}
    merged_property = {**property_details, **{k: v for k, v in provided.items() if v not in (None, "", [])}}
    search_context = build_search_context(
        geo,
        merged_property,
        primary_radius_miles=primary_radius,
    )

    return {
        "intake": parsed,
        "target_property": {
            **merged_property,
            "address": address,
            "city": parsed.get("city") or geo.get("city") or merged_property.get("city"),
            "state": parsed.get("state") or geo.get("state") or merged_property.get("state"),
            "zipcode": parsed.get("zipcode") or geo.get("zipcode") or merged_property.get("zipcode"),
        },
        "geo": geo,
        "radius_miles": radius,
        "primary_radius_miles": primary_radius,
        "timeframe_months": timeframe,
        "search_context": search_context,
        "status": "researching",
        "errors": state.get("errors", []),
    }
