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


def build_search_context(geo: dict[str, Any], property_details: dict | None = None) -> str:
    """Human-readable context string for research prompts."""
    parts = [
        f"Address: {geo.get('display_name', 'unknown')}",
        f"Coordinates: {geo.get('lat')}, {geo.get('lng')}",
        f"Search radius: {geo.get('radius_miles', 5)} miles",
        f"City: {geo.get('city')}, State: {geo.get('state')}, ZIP: {geo.get('zipcode')}",
        f"County: {geo.get('county')}",
    ]
    if property_details:
        beds = property_details.get("bedrooms", "?")
        baths = property_details.get("bathrooms", "?")
        sqft = property_details.get("sqft", "?")
        ptype = property_details.get("property_type", "?")
        parts.append(f"Subject property: {beds}bd/{baths}ba, {sqft} sqft, {ptype}")
    return "\n".join(parts)
