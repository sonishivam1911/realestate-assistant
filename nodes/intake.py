"""Intake node — parse user message, geocode address."""

import json
import logging
import os

from output_parser import ActionParser
from prompts.cma_intake import INTAKE_SYSTEM, INTAKE_USER
from services.geocode import build_search_context, geocode_address
from services.openrouter_client import chat_completion
from workflow.cma_state import CMAState

from nodes.config import DEFAULT_RADIUS_MILES, TIMEFRAME_MONTHS

logger = logging.getLogger(__name__)
_parser = ActionParser(use_json_repair=True)


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
    radius = float(parsed.get("radius_miles") or state.get("radius_miles") or DEFAULT_RADIUS_MILES)
    timeframe = int(parsed.get("timeframe_months") or TIMEFRAME_MONTHS)
    property_details = parsed.get("property") or state.get("target_property") or {}

    geo = geocode_address(address)
    if geo.get("error"):
        return {
            "errors": state.get("errors", []) + [geo["error"]],
            "status": "failed",
        }

    geo["radius_miles"] = radius
    search_context = build_search_context(geo, property_details)

    return {
        "intake": parsed,
        "target_property": {
            "address": address,
            "city": parsed.get("city") or geo.get("city"),
            "state": parsed.get("state") or geo.get("state"),
            "zipcode": parsed.get("zipcode") or geo.get("zipcode"),
            **property_details,
        },
        "geo": geo,
        "radius_miles": radius,
        "timeframe_months": timeframe,
        "search_context": search_context,
        "status": "researching",
        "errors": state.get("errors", []),
    }
