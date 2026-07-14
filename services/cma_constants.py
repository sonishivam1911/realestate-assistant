"""CMA methodology constants — Homes.com / pro-style selection rules."""

# Prefer tight primary search; widen to radius_miles for fallbacks.
PRIMARY_RADIUS_MILES = 2.0
DEFAULT_OUTER_RADIUS_MILES = 5.0
DEFAULT_TIMEFRAME_MONTHS = 3

# Similarity / bucketing
SQFT_TOLERANCE_RATIO = 0.15
PRIMARY_MIN_SIMILARITY_SCORE = 60.0
MIN_PRIMARY_COMPS = 3
TARGET_SOLD_COMPS = 8
MAX_ACTIVE_COMPS = 6
MAX_PENDING_COMPS = 4

# Scoring weights (sum to 100)
WEIGHT_ARCHITECTURAL_STYLE = 25.0
WEIGHT_SQUARE_FOOTAGE = 20.0
WEIGHT_BEDROOMS = 15.0
WEIGHT_BATHROOMS = 10.0
WEIGHT_DISTANCE = 15.0
WEIGHT_RECENCY = 10.0
WEIGHT_AMENITIES = 5.0

# Style aliases normalized before matching
ARCHITECTURAL_STYLE_ALIASES = {
    "ranch": "ranch",
    "rambler": "ranch",
    "brick ranch": "ranch",
    "colonial": "colonial",
    "center hall colonial": "colonial",
    "cape": "cape_cod",
    "cape cod": "cape_cod",
    "split": "split_level",
    "split level": "split_level",
    "bi-level": "split_level",
    "bilevel": "split_level",
    "contemporary": "contemporary",
    "modern": "contemporary",
    "tudor": "tudor",
    "victorian": "victorian",
    "craftsman": "craftsman",
    "bungalow": "bungalow",
    "townhouse": "townhouse",
    "townhome": "townhouse",
    "condo": "condo",
    "apartment": "condo",
}

SUBJECT_ENRICH_FIELDS = (
    "sqft",
    "year_built",
    "architectural_style",
    "property_type",
    "lot_sqft",
    "garage_spaces",
    "amenities",
    "bedrooms",
    "bathrooms",
    "asking_price",
)

COMP_BUCKET_PRIMARY = "primary"
COMP_BUCKET_SUPPORTING = "supporting"

LISTING_STATUS_SOLD = "sold"
LISTING_STATUS_PENDING = "pending"
LISTING_STATUS_ACTIVE = "active"
