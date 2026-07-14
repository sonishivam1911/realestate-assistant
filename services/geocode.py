"""Geocode address to lat/lng and 5-mile search context."""

import os
from typing import Any

import requests


def geocode_address(address: str) -> dict[str, Any]:
    """
    Geocode via OpenStreetMap Nominatim (free, no key).
    Returns {lat, lng, display_name, city, state, zipcode, county}.
    """
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": address, "format": "json", "addressdetails": 1, "limit": 1},
        headers={"User-Agent": os.getenv("GEOCODE_USER_AGENT", "realestate-cma/1.0")},
        timeout=15,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return {"error": f"Could not geocode: {address}"}

    hit = results[0]
    addr = hit.get("address", {})
    return {
        "lat": float(hit["lat"]),
        "lng": float(hit["lon"]),
        "display_name": hit.get("display_name", address),
        "city": addr.get("city") or addr.get("town") or addr.get("village", ""),
        "state": addr.get("state", ""),
        "zipcode": addr.get("postcode", ""),
        "county": addr.get("county", ""),
        "radius_miles": float(os.getenv("CMA_DEFAULT_RADIUS_MILES", "5")),
    }


def build_search_context(
    geo: dict[str, Any],
    property_details: dict | None = None,
    *,
    primary_radius_miles: float | None = None,
) -> str:
    """Human-readable context string for research prompts."""
    outer_radius = geo.get("radius_miles", 5)
    parts = [
        f"Address: {geo.get('display_name', 'unknown')}",
        f"Coordinates: {geo.get('lat')}, {geo.get('lng')}",
        f"Primary search radius: {primary_radius_miles or min(2.0, float(outer_radius))} miles",
        f"Outer search radius: {outer_radius} miles",
        f"City: {geo.get('city')}, State: {geo.get('state')}, ZIP: {geo.get('zipcode')}",
        f"County: {geo.get('county')}",
    ]
    if property_details:
        beds = property_details.get("bedrooms", "?")
        baths = property_details.get("bathrooms", "?")
        sqft = property_details.get("sqft", "?")
        ptype = property_details.get("property_type", "?")
        style = property_details.get("architectural_style", "?")
        year_built = property_details.get("year_built", "?")
        lot_sqft = property_details.get("lot_sqft", "?")
        garage = property_details.get("garage_spaces", "?")
        amenities = property_details.get("amenities") or []
        if isinstance(amenities, list):
            amenity_text = ", ".join(str(item) for item in amenities) or "none listed"
        else:
            amenity_text = str(amenities)
        asking = property_details.get("asking_price", "?")
        parts.append(
            "Subject property: "
            f"{beds}bd/{baths}ba, {sqft} sqft, type={ptype}, style={style}, "
            f"year_built={year_built}, lot_sqft={lot_sqft}, garage={garage}, "
            f"amenities=[{amenity_text}], asking_price={asking}"
        )
        parts.append(
            "Style policy: prefer same architectural style for primary comps; "
            "include other styles as supporting comps with dollar adjustments."
        )
    return "\n".join(parts)
