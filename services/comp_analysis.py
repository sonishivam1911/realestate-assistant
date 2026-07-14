"""Score, bucket, and normalize CMA comps (deterministic post-LLM analysis)."""

from datetime import date, datetime
from typing import Any

from services.cma_constants import (
    ARCHITECTURAL_STYLE_ALIASES,
    COMP_BUCKET_PRIMARY,
    COMP_BUCKET_SUPPORTING,
    LISTING_STATUS_ACTIVE,
    LISTING_STATUS_PENDING,
    LISTING_STATUS_SOLD,
    MIN_PRIMARY_COMPS,
    PRIMARY_MIN_SIMILARITY_SCORE,
    PRIMARY_RADIUS_MILES,
    SQFT_TOLERANCE_RATIO,
    SUBJECT_ENRICH_FIELDS,
    WEIGHT_AMENITIES,
    WEIGHT_ARCHITECTURAL_STYLE,
    WEIGHT_BATHROOMS,
    WEIGHT_BEDROOMS,
    WEIGHT_DISTANCE,
    WEIGHT_RECENCY,
    WEIGHT_SQUARE_FOOTAGE,
)


def normalize_architectural_style(style: Any) -> str | None:
    if style is None:
        return None
    text = str(style).strip().lower()
    if not text or text in {"unknown", "other", "n/a", "none"}:
        return None
    if text in ARCHITECTURAL_STYLE_ALIASES:
        return ARCHITECTURAL_STYLE_ALIASES[text]
    for alias, canonical in ARCHITECTURAL_STYLE_ALIASES.items():
        if alias in text:
            return canonical
    return text.replace(" ", "_")


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    number = _as_float(value)
    if number is None:
        return None
    return int(round(number))


def _normalize_amenities(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [part.strip().lower() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    return []


def _parse_sold_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def styles_match(subject_style: str | None, comp_style: str | None) -> bool:
    subject = normalize_architectural_style(subject_style)
    comp = normalize_architectural_style(comp_style)
    if not subject or not comp:
        return False
    return subject == comp


def _score_style(subject: dict, comp: dict) -> tuple[float, str]:
    subject_style = subject.get("architectural_style")
    comp_style = comp.get("architectural_style")
    if styles_match(subject_style, comp_style):
        return WEIGHT_ARCHITECTURAL_STYLE, "architectural style matches subject"
    if not normalize_architectural_style(subject_style) or not normalize_architectural_style(comp_style):
        return WEIGHT_ARCHITECTURAL_STYLE * 0.4, "style unknown — partial credit"
    return 0.0, (
        f"style mismatch ({normalize_architectural_style(comp_style)} vs "
        f"{normalize_architectural_style(subject_style)})"
    )


def _score_sqft(subject: dict, comp: dict) -> tuple[float, str]:
    subject_sqft = _as_float(subject.get("sqft"))
    comp_sqft = _as_float(comp.get("sqft"))
    if not subject_sqft or not comp_sqft or subject_sqft <= 0:
        return WEIGHT_SQUARE_FOOTAGE * 0.5, "sqft incomplete — partial credit"
    ratio = abs(comp_sqft - subject_sqft) / subject_sqft
    if ratio <= SQFT_TOLERANCE_RATIO:
        return WEIGHT_SQUARE_FOOTAGE, f"sqft within {int(SQFT_TOLERANCE_RATIO * 100)}%"
    if ratio <= SQFT_TOLERANCE_RATIO * 2:
        return WEIGHT_SQUARE_FOOTAGE * 0.5, f"sqft {ratio:.0%} off subject"
    return 0.0, f"sqft {ratio:.0%} off subject"


def _score_count_field(
    subject: dict,
    comp: dict,
    field_name: str,
    weight: float,
) -> tuple[float, str]:
    subject_value = _as_float(subject.get(field_name))
    comp_value = _as_float(comp.get(field_name))
    if subject_value is None or comp_value is None:
        return weight * 0.5, f"{field_name} incomplete — partial credit"
    delta = abs(comp_value - subject_value)
    if delta == 0:
        return weight, f"{field_name} exact match"
    if delta <= 1:
        return weight * 0.6, f"{field_name} within 1"
    return 0.0, f"{field_name} mismatch ({comp_value} vs {subject_value})"


def _score_distance(comp: dict, primary_radius_miles: float) -> tuple[float, str]:
    distance = _as_float(comp.get("distance_miles"))
    if distance is None:
        return WEIGHT_DISTANCE * 0.5, "distance unknown — partial credit"
    if distance <= primary_radius_miles:
        return WEIGHT_DISTANCE, f"within primary {primary_radius_miles:g}-mile radius"
    if distance <= primary_radius_miles * 2.5:
        return WEIGHT_DISTANCE * 0.55, f"{distance:.1f} mi — outer-radius fallback"
    return WEIGHT_DISTANCE * 0.2, f"{distance:.1f} mi — distant"


def _score_recency(comp: dict, timeframe_months: int) -> tuple[float, str]:
    sold_on = _parse_sold_date(comp.get("sold_date") or comp.get("close_date"))
    if not sold_on:
        status = str(comp.get("status") or "").lower()
        if status in {LISTING_STATUS_ACTIVE, LISTING_STATUS_PENDING}:
            return WEIGHT_RECENCY * 0.7, f"{status} listing — competition context"
        return WEIGHT_RECENCY * 0.4, "sale date unknown — partial credit"
    age_days = (date.today() - sold_on).days
    window_days = max(timeframe_months, 1) * 30
    if age_days <= window_days:
        return WEIGHT_RECENCY, f"sold {age_days}d ago (within window)"
    if age_days <= window_days * 2:
        return WEIGHT_RECENCY * 0.5, f"sold {age_days}d ago (stale)"
    return 0.0, f"sold {age_days}d ago (too old)"


def _score_amenities(subject: dict, comp: dict) -> tuple[float, str]:
    subject_amenities = set(_normalize_amenities(subject.get("amenities")))
    if subject.get("pool") is True:
        subject_amenities.add("pool")
    garage = _as_float(subject.get("garage_spaces"))
    if garage and garage >= 1:
        subject_amenities.add("garage")

    comp_amenities = set(_normalize_amenities(comp.get("amenities")))
    if comp.get("pool") is True:
        comp_amenities.add("pool")
    comp_garage = _as_float(comp.get("garage_spaces"))
    if comp_garage and comp_garage >= 1:
        comp_amenities.add("garage")

    if not subject_amenities:
        return WEIGHT_AMENITIES * 0.5, "subject amenities sparse — partial credit"
    overlap = subject_amenities & comp_amenities
    ratio = len(overlap) / len(subject_amenities)
    return WEIGHT_AMENITIES * ratio, f"amenity overlap {len(overlap)}/{len(subject_amenities)}"


def score_comparable(
    subject: dict[str, Any],
    comp: dict[str, Any],
    *,
    primary_radius_miles: float = PRIMARY_RADIUS_MILES,
    timeframe_months: int = 3,
) -> dict[str, Any]:
    """Attach similarity score + explainability fields to a comp copy."""
    scored = dict(comp)
    parts = [
        _score_style(subject, scored),
        _score_sqft(subject, scored),
        _score_count_field(subject, scored, "bedrooms", WEIGHT_BEDROOMS),
        _score_count_field(subject, scored, "bathrooms", WEIGHT_BATHROOMS),
        _score_distance(scored, primary_radius_miles),
        _score_recency(scored, timeframe_months),
        _score_amenities(subject, scored),
    ]
    total = round(sum(points for points, _ in parts), 1)
    reasons = [reason for _, reason in parts]
    style_matched = styles_match(
        subject.get("architectural_style"),
        scored.get("architectural_style"),
    )

    scored["similarity_score"] = total
    scored["style_match"] = style_matched
    scored["score_breakdown"] = reasons
    scored["keep_reason"] = "; ".join(reasons[:3])
    if not style_matched and normalize_architectural_style(subject.get("architectural_style")):
        scored["downweight_reason"] = reasons[0]
    else:
        scored["downweight_reason"] = scored.get("downweight_reason") or ""

    sold_price = _as_float(scored.get("sold_price") or scored.get("list_price"))
    adjusted = _as_float(scored.get("adjusted_price"))
    if adjusted is None and sold_price is not None:
        adjustment_total = 0.0
        for row in scored.get("adjustments") or []:
            amount = _as_float(row.get("amount")) or 0.0
            adjustment_total += amount
        scored["adjusted_price"] = round(sold_price + adjustment_total, 2)
        scored["adjustment_total"] = round(adjustment_total, 2)
    elif adjusted is not None:
        scored["adjustment_total"] = round(
            adjusted - (sold_price or adjusted),
            2,
        )

    sqft = _as_float(scored.get("sqft"))
    if sold_price and sqft and sqft > 0 and not scored.get("price_per_sqft"):
        scored["price_per_sqft"] = round(sold_price / sqft, 2)

    return scored


def _is_primary_candidate(comp: dict[str, Any], subject: dict[str, Any]) -> bool:
    if float(comp.get("similarity_score") or 0) < PRIMARY_MIN_SIMILARITY_SCORE:
        return False
    subject_style = normalize_architectural_style(subject.get("architectural_style"))
    if subject_style and not comp.get("style_match"):
        return False
    return True


def analyze_comp_research(
    subject: dict[str, Any],
    raw_research: dict[str, Any],
    *,
    primary_radius_miles: float = PRIMARY_RADIUS_MILES,
    timeframe_months: int = 3,
) -> dict[str, Any]:
    """
    Normalize LLM comp research into primary/supporting sold buckets plus
    active/pending competition sets.
    """
    research = dict(raw_research or {})

    sold_raw = list(research.get("sold_comps") or research.get("comps") or [])
    pending_raw = list(research.get("pending_comps") or [])
    active_raw = list(research.get("active_comps") or [])

    sold_scored = [
        score_comparable(
            subject,
            {**comp, "status": comp.get("status") or LISTING_STATUS_SOLD},
            primary_radius_miles=primary_radius_miles,
            timeframe_months=timeframe_months,
        )
        for comp in sold_raw
        if isinstance(comp, dict) and comp.get("address")
    ]
    sold_scored.sort(key=lambda item: float(item.get("similarity_score") or 0), reverse=True)

    primary_comps: list[dict[str, Any]] = []
    supporting_comps: list[dict[str, Any]] = []

    for comp in sold_scored:
        if _is_primary_candidate(comp, subject):
            enriched = {**comp, "bucket": COMP_BUCKET_PRIMARY}
            primary_comps.append(enriched)
        else:
            enriched = {**comp, "bucket": COMP_BUCKET_SUPPORTING}
            supporting_comps.append(enriched)

    # Homes/pro fallback: if too few same-style primaries, elevate best supporting.
    elevated_count = 0
    if len(primary_comps) < MIN_PRIMARY_COMPS:
        needed = MIN_PRIMARY_COMPS - len(primary_comps)
        elevated: list[dict[str, Any]] = []
        remaining_supporting: list[dict[str, Any]] = []
        for comp in supporting_comps:
            if len(elevated) < needed and float(comp.get("similarity_score") or 0) >= (
                PRIMARY_MIN_SIMILARITY_SCORE * 0.75
            ):
                elevated.append(
                    {
                        **comp,
                        "bucket": COMP_BUCKET_PRIMARY,
                        "elevated_from_supporting": True,
                        "downweight_reason": (
                            comp.get("downweight_reason")
                            or "elevated fallback — style/size imperfect match; use adjustments"
                        ),
                    }
                )
                elevated_count += 1
            else:
                remaining_supporting.append(comp)
        primary_comps.extend(elevated)
        supporting_comps = remaining_supporting

    pending_scored = [
        score_comparable(
            subject,
            {**comp, "status": LISTING_STATUS_PENDING},
            primary_radius_miles=primary_radius_miles,
            timeframe_months=timeframe_months,
        )
        for comp in pending_raw
        if isinstance(comp, dict) and comp.get("address")
    ]
    active_scored = [
        score_comparable(
            subject,
            {**comp, "status": LISTING_STATUS_ACTIVE},
            primary_radius_miles=primary_radius_miles,
            timeframe_months=timeframe_months,
        )
        for comp in active_raw
        if isinstance(comp, dict) and comp.get("address")
    ]
    pending_scored.sort(key=lambda item: float(item.get("similarity_score") or 0), reverse=True)
    active_scored.sort(key=lambda item: float(item.get("similarity_score") or 0), reverse=True)

    flattened_sold = primary_comps + supporting_comps
    style_matches = sum(1 for comp in sold_scored if comp.get("style_match"))

    research.update(
        {
            "sold_comps": flattened_sold,
            "primary_comps": primary_comps,
            "supporting_comps": supporting_comps,
            "pending_comps": pending_scored,
            "active_comps": active_scored,
            # Backward-compatible flat list for DB persistence / older readers.
            "comps": flattened_sold,
            "methodology": {
                "style_policy": "prefer_same_style_with_fallbacks_and_adjustments",
                "primary_radius_miles": primary_radius_miles,
                "sqft_tolerance_ratio": SQFT_TOLERANCE_RATIO,
                "primary_min_similarity_score": PRIMARY_MIN_SIMILARITY_SCORE,
                "min_primary_comps": MIN_PRIMARY_COMPS,
                "style_matched_sold_count": style_matches,
                "elevated_supporting_count": elevated_count,
            },
            "data_quality": research.get("data_quality")
            or ("high" if len(primary_comps) >= MIN_PRIMARY_COMPS else "medium"),
        }
    )
    return research


def merge_subject_details(
    base: dict[str, Any],
    enrichment: dict[str, Any],
) -> dict[str, Any]:
    """Prefer user-provided values; fill gaps from enrichment."""
    merged = dict(base or {})
    incoming = dict(enrichment or {})

    for key, value in incoming.items():
        if value in (None, "", [], {}):
            continue
        existing = merged.get(key)
        if existing in (None, "", [], {}, "?"):
            merged[key] = value
            continue
        if key == "amenities":
            merged[key] = sorted(
                set(_normalize_amenities(existing)) | set(_normalize_amenities(value))
            )
        elif key == "architectural_style":
            merged[key] = normalize_architectural_style(existing) or normalize_architectural_style(
                value
            )
        # else keep user/base value

    if "architectural_style" in merged:
        merged["architectural_style"] = normalize_architectural_style(
            merged.get("architectural_style")
        )

    if merged.get("amenities"):
        merged["amenities"] = _normalize_amenities(merged.get("amenities"))

    # Convenience booleans for scoring
    amenities = set(merged.get("amenities") or [])
    if "pool" in amenities:
        merged["pool"] = True
    garage = _as_int(merged.get("garage_spaces"))
    if garage is not None:
        merged["garage_spaces"] = garage

    for numeric_key in ("sqft", "year_built", "lot_sqft", "bedrooms", "bathrooms", "asking_price"):
        if numeric_key in merged:
            number = _as_float(merged.get(numeric_key))
            if number is not None:
                merged[numeric_key] = int(number) if numeric_key in {
                    "sqft",
                    "year_built",
                    "lot_sqft",
                } else number

    return merged


def missing_subject_fields(subject: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field_name in SUBJECT_ENRICH_FIELDS:
        value = subject.get(field_name)
        if value in (None, "", [], {}, "?"):
            missing.append(field_name)
    return missing
