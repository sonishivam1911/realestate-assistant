"""Integration test — CMA LangGraph fan-out pipeline with mocked LLM/geocode."""

import json
from unittest.mock import patch

import pytest

from workflow.cma_graph import CMAGraph

USER_MESSAGE = (
    "102 Albury way, North Brunswick NJ, Condo, "
    "3 bedroom and 1 bath and 1100 - 1200 sqft"
)

INTAKE_JSON = {
    "address": "102 Albury Way, North Brunswick, NJ",
    "city": "North Brunswick",
    "state": "NJ",
    "zipcode": "08902",
    "radius_miles": 5,
    "timeframe_months": 3,
    "property": {
        "property_type": "condo",
        "architectural_style": "condo",
        "bedrooms": 3,
        "bathrooms": 1,
        "sqft": 1150,
        "year_built": 1990,
        "garage_spaces": 1,
        "amenities": ["garage"],
        "asking_price": 330000,
    },
}

GEOCODE = {
    "lat": 40.45,
    "lng": -74.48,
    "city": "North Brunswick",
    "state": "NJ",
    "zipcode": "08902",
    "county": "Middlesex County",
    "display_name": "102 Albury Way, North Brunswick, NJ 08902",
}

COMP_JSON = {
    "sold_comps": [
        {
            "address": "98 Albury Way",
            "sold_price": 325000,
            "sold_date": "2026-05-01",
            "sqft": 1150,
            "bedrooms": 3,
            "bathrooms": 1,
            "architectural_style": "condo",
            "property_type": "condo",
            "distance_miles": 0.2,
            "amenities": ["garage"],
            "garage_spaces": 1,
            "adjustments": [],
        },
        {
            "address": "110 Albury Way",
            "sold_price": 318000,
            "sold_date": "2026-04-12",
            "sqft": 1120,
            "bedrooms": 3,
            "bathrooms": 1,
            "architectural_style": "condo",
            "property_type": "condo",
            "distance_miles": 0.3,
            "amenities": ["garage"],
            "garage_spaces": 1,
            "adjustments": [],
        },
        {
            "address": "200 Different St",
            "sold_price": 340000,
            "sold_date": "2026-03-20",
            "sqft": 1300,
            "bedrooms": 3,
            "bathrooms": 2,
            "architectural_style": "townhouse",
            "property_type": "townhouse",
            "distance_miles": 1.4,
            "amenities": [],
            "adjustments": [
                {
                    "factor": "style",
                    "amount": -10000,
                    "direction": "comp_superior",
                    "note": "townhouse vs condo",
                }
            ],
        },
    ],
    "pending_comps": [],
    "active_comps": [
        {
            "address": "105 Albury Way",
            "list_price": 335000,
            "sqft": 1160,
            "bedrooms": 3,
            "bathrooms": 1,
            "architectural_style": "condo",
            "distance_miles": 0.25,
        }
    ],
    "summary": "Nearby condo comps support mid-320s.",
    "data_quality": "medium",
}

MARKET_JSON = {
    "market_type": "balanced",
    "summary": "Stable condo market in North Brunswick.",
}

MACRO_JSON = {
    "summary": "Mortgage rates steady; inflation moderating.",
}

SYNTHESIS_JSON = {
    "executive_summary": "Subject condo estimated at $320k–$335k.",
    "recommended_list_price": 328000,
    "markdown_report": "# CMA Report\n\nRecommended list price: **$328,000**",
}

ENRICH_JSON = {
    "sqft": 1150,
    "year_built": 1990,
    "architectural_style": "condo",
    "property_type": "condo",
    "garage_spaces": 1,
    "amenities": ["garage"],
    "enrichment_confidence": "high",
    "enrichment_notes": "Complete from listing",
}


@pytest.fixture
def mock_external_services():
    def fake_chat_completion(**kwargs):
        user_prompt = kwargs.get("user_prompt") or ""
        if "Parse this real estate CMA request" in user_prompt:
            return json.dumps(INTAKE_JSON)
        return json.dumps(SYNTHESIS_JSON)

    with (
        patch(
            "nodes.intake.chat_completion",
            side_effect=fake_chat_completion,
        ),
        patch(
            "nodes.synthesis.chat_completion",
            side_effect=fake_chat_completion,
        ),
        patch(
            "nodes.intake.geocode_address",
            return_value=GEOCODE,
        ),
        patch(
            "nodes.subject_enrich.chat_with_web_search",
            return_value={"content": json.dumps(ENRICH_JSON), "citations": []},
        ),
        patch(
            "nodes.comp_research.chat_with_web_search",
            return_value={"content": json.dumps(COMP_JSON), "citations": []},
        ),
        patch(
            "nodes.market_pulse.chat_with_web_search",
            return_value={"content": json.dumps(MARKET_JSON), "citations": []},
        ),
        patch(
            "nodes.macro_context.chat_with_web_search",
            return_value={"content": json.dumps(MACRO_JSON), "citations": []},
        ),
    ):
        yield


def test_cma_graph_fan_out_completes(mock_external_services):
    graph = CMAGraph()
    state = graph.run(USER_MESSAGE, radius_miles=5.0)

    assert state.get("status") == "complete"
    assert state.get("errors") == []
    assert state.get("target_property", {}).get("address")
    assert state.get("target_property", {}).get("architectural_style") == "condo"
    assert state.get("primary_radius_miles") == 2.0
    research = state.get("comp_research") or {}
    assert research.get("primary_comps")
    assert research.get("comps")
    assert research.get("active_comps")
    assert state.get("market_pulse", {}).get("market_type")
    assert state.get("macro_context", {}).get("summary")
    report = state.get("cma_report") or {}
    assert report.get("recommended_list_price") == 328000
    assert "328,000" in (report.get("markdown_report") or "")


def test_cma_graph_intake_geocode_failure():
    with patch(
        "nodes.intake.chat_completion",
        return_value=json.dumps(INTAKE_JSON),
    ), patch(
        "nodes.intake.geocode_address",
        return_value={"error": "Address not found"},
    ):
        state = CMAGraph().run(USER_MESSAGE)

    assert state.get("status") == "complete"
    assert any("geocode" in e.lower() or "address" in e.lower() for e in state.get("errors") or [])
    assert (state.get("cma_report") or {}).get("verdict") == "insufficient_data"
