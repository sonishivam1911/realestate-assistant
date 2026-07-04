import operator
from typing import Annotated, Any, TypedDict


def _merge_lists(left: list, right: list) -> list:
    return (left or []) + (right or [])


class CMAState(TypedDict, total=False):
    """State for CMA LangGraph workflow with fan-out research branches."""

    # Chat / session
    conversation_id: str
    user_message: str
    assistant_message: str

    # Intake
    intake: dict[str, Any]
    target_property: dict[str, Any]
    geo: dict[str, Any]
    radius_miles: float
    timeframe_months: int
    search_context: str

    # Fan-out research branches (written by parallel nodes)
    comp_research: dict[str, Any]
    market_pulse: dict[str, Any]
    macro_context: dict[str, Any]

    comp_citations: Annotated[list[dict], _merge_lists]
    market_citations: Annotated[list[dict], _merge_lists]
    macro_citations: Annotated[list[dict], _merge_lists]

    # Synthesis output
    cma_report: dict[str, Any]
    all_citations: list[dict]

    # Workflow meta
    status: str  # pending | researching | synthesizing | complete | failed
    errors: Annotated[list[str], _merge_lists]
    workflow_start_time: str
    workflow_end_time: str
