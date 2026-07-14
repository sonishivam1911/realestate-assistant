"""
CMA workflow with LangGraph fan-out.

  intake → subject_enrich
    ├─[Send]─► comp_research  ─┐
    ├─[Send]─► market_pulse   ─┼─► merge_research ─► synthesis ─► END
    └─[Send]─► macro_context  ─┘
"""

from datetime import datetime

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from nodes.comp_research import comp_research_node
from nodes.intake import intake_node
from nodes.macro_context import macro_context_node
from nodes.market_pulse import market_pulse_node
from nodes.merge_research import merge_research_node
from nodes.subject_enrich import subject_enrich_node
from nodes.synthesis import synthesis_node
from workflow.cma_state import CMAState


def _fan_out_research(state: CMAState) -> list[Send]:
    if state.get("status") == "failed":
        return [Send("synthesis", state)]
    return [
        Send("comp_research", state),
        Send("market_pulse", state),
        Send("macro_context", state),
    ]


class CMAGraph:
    def __init__(self):
        self.graph = self._build().compile()

    def _build(self) -> StateGraph:
        g = StateGraph(CMAState)

        g.add_node("intake", intake_node)
        g.add_node("subject_enrich", subject_enrich_node)
        g.add_node("comp_research", comp_research_node)
        g.add_node("market_pulse", market_pulse_node)
        g.add_node("macro_context", macro_context_node)
        g.add_node("merge_research", merge_research_node)
        g.add_node("synthesis", synthesis_node)

        g.set_entry_point("intake")
        g.add_edge("intake", "subject_enrich")
        g.add_conditional_edges(
            "subject_enrich",
            _fan_out_research,
            ["comp_research", "market_pulse", "macro_context", "synthesis"],
        )
        g.add_edge("comp_research", "merge_research")
        g.add_edge("market_pulse", "merge_research")
        g.add_edge("macro_context", "merge_research")
        g.add_edge("merge_research", "synthesis")
        g.add_edge("synthesis", END)

        return g

    def run(
        self,
        user_message: str,
        *,
        conversation_id: str | None = None,
        radius_miles: float = 5.0,
        target_property: dict | None = None,
    ) -> CMAState:
        initial: CMAState = {
            "user_message": user_message,
            "conversation_id": conversation_id or "",
            "radius_miles": radius_miles,
            "target_property": target_property or {},
            "status": "pending",
            "errors": [],
            "workflow_start_time": datetime.utcnow().isoformat(),
        }
        result = self.graph.invoke(initial)
        result["workflow_end_time"] = datetime.utcnow().isoformat()
        return result
