"""Macro context node — inflation, rates (fan-out branch)."""

from output_parser import ActionParser
from prompts.cma_macro_context import MACRO_CONTEXT_SYSTEM, MACRO_CONTEXT_USER
from services.openrouter_client import chat_with_web_search
from workflow.cma_state import CMAState

from nodes.config import MODEL_RESEARCH

_parser = ActionParser(use_json_repair=True)


def macro_context_node(state: CMAState) -> dict:
    prompt = MACRO_CONTEXT_USER.format(search_context=state["search_context"])

    result = chat_with_web_search(
        model=MODEL_RESEARCH,
        system_prompt=MACRO_CONTEXT_SYSTEM,
        user_prompt=prompt,
        temperature=0.2,
        max_tokens=3072,
    )

    parsed = _parser.safe_json_parse(result["content"]) or {
        "summary": result["content"],
    }

    return {
        "macro_context": parsed,
        "macro_citations": result["citations"],
    }
