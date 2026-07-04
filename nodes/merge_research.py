"""Merge parallel fan-out branch outputs before synthesis."""

from workflow.cma_state import CMAState


def merge_research_node(state: CMAState) -> dict:
    """No-op merge — LangGraph reducer on state keys handles fan-in."""
    return {"status": "synthesizing"}
