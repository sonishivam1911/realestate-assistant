"""Unit tests for CMA comp scoring / style bucketing."""

from services.comp_analysis import (
    analyze_comp_research,
    merge_subject_details,
    normalize_architectural_style,
    score_comparable,
)


def test_normalize_architectural_style_aliases():
    assert normalize_architectural_style("Brick Ranch") == "ranch"
    assert normalize_architectural_style("Center Hall Colonial") == "colonial"
    assert normalize_architectural_style(None) is None


def test_merge_subject_details_prefers_user_values():
    merged = merge_subject_details(
        {"sqft": 1400, "architectural_style": "ranch", "amenities": ["garage"]},
        {
            "sqft": 9999,
            "year_built": 1960,
            "architectural_style": "colonial",
            "amenities": ["pool"],
        },
    )
    assert merged["sqft"] == 1400
    assert merged["architectural_style"] == "ranch"
    assert merged["year_built"] == 1960
    assert set(merged["amenities"]) == {"garage", "pool"}


def test_same_style_scores_higher_than_mismatch():
    subject = {
        "architectural_style": "ranch",
        "sqft": 1400,
        "bedrooms": 3,
        "bathrooms": 2,
        "amenities": ["pool", "garage"],
        "garage_spaces": 2,
    }
    ranch = score_comparable(
        subject,
        {
            "address": "1 Ranch Rd",
            "architectural_style": "ranch",
            "sqft": 1380,
            "bedrooms": 3,
            "bathrooms": 2,
            "distance_miles": 1.2,
            "sold_date": "2026-06-01",
            "sold_price": 580000,
            "amenities": ["pool", "garage"],
            "garage_spaces": 2,
        },
    )
    colonial = score_comparable(
        subject,
        {
            "address": "2 Colonial Ln",
            "architectural_style": "colonial",
            "sqft": 1380,
            "bedrooms": 3,
            "bathrooms": 2,
            "distance_miles": 1.2,
            "sold_date": "2026-06-01",
            "sold_price": 590000,
            "amenities": ["garage"],
            "garage_spaces": 2,
        },
    )
    assert ranch["similarity_score"] > colonial["similarity_score"]
    assert ranch["style_match"] is True
    assert colonial["style_match"] is False


def test_analyze_comp_research_buckets_and_elevates_fallbacks():
    subject = {
        "architectural_style": "ranch",
        "sqft": 1400,
        "bedrooms": 3,
        "bathrooms": 2,
        "amenities": ["pool"],
    }
    raw = {
        "sold_comps": [
            {
                "address": "10 Ranch Ave",
                "architectural_style": "ranch",
                "sqft": 1410,
                "bedrooms": 3,
                "bathrooms": 2,
                "distance_miles": 0.8,
                "sold_date": "2026-05-15",
                "sold_price": 575000,
                "amenities": ["pool"],
                "adjustments": [],
            },
            {
                "address": "20 Colonial St",
                "architectural_style": "colonial",
                "sqft": 1500,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "distance_miles": 1.1,
                "sold_date": "2026-04-20",
                "sold_price": 610000,
                "amenities": [],
                "adjustments": [
                    {
                        "factor": "style",
                        "amount": -15000,
                        "direction": "comp_superior",
                        "note": "colonial vs ranch",
                    }
                ],
            },
            {
                "address": "30 Far Colonial",
                "architectural_style": "colonial",
                "sqft": 1600,
                "bedrooms": 3,
                "bathrooms": 2,
                "distance_miles": 1.5,
                "sold_date": "2026-03-10",
                "sold_price": 560000,
                "amenities": ["pool"],
                "adjustments": [],
            },
        ],
        "pending_comps": [
            {
                "address": "40 Pending Rd",
                "list_price": 599000,
                "sqft": 1400,
                "bedrooms": 3,
                "bathrooms": 2,
                "architectural_style": "ranch",
                "distance_miles": 1.0,
            }
        ],
        "active_comps": [
            {
                "address": "50 Active Rd",
                "list_price": 619000,
                "sqft": 1450,
                "bedrooms": 3,
                "bathrooms": 2,
                "architectural_style": "colonial",
                "distance_miles": 1.3,
            }
        ],
        "summary": "mixed styles",
    }

    analyzed = analyze_comp_research(subject, raw, primary_radius_miles=2.0, timeframe_months=3)

    assert analyzed["primary_comps"]
    assert analyzed["primary_comps"][0]["address"] == "10 Ranch Ave"
    assert analyzed["primary_comps"][0]["bucket"] == "primary"
    # Need at least 3 primary via elevation when only one ranch exists.
    assert len(analyzed["primary_comps"]) >= 3
    assert any(comp.get("elevated_from_supporting") for comp in analyzed["primary_comps"])
    assert analyzed["pending_comps"]
    assert analyzed["active_comps"]
    assert analyzed["comps"] == analyzed["primary_comps"] + analyzed["supporting_comps"]
    colonial = next(c for c in analyzed["comps"] if c["address"] == "20 Colonial St")
    assert colonial["adjusted_price"] == 595000
