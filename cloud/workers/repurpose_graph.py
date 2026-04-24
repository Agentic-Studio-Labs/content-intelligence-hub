from typing import Any, Annotated, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from shared.providers.base import LLMProvider
from workers.repurpose_tools import GENERATORS, analyze_content, assess_quality


class RepurposeState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    source_content: dict[str, Any]
    requested_formats: list[str]
    tone: str
    custom_instructions: dict[str, str]
    analysis: dict[str, Any]
    generated_content: dict[str, str]
    quality_scores: dict[str, float]
    errors: list[str]
    current_step: str


def _analyze_node(state: RepurposeState, provider: LLMProvider) -> dict:
    analysis = analyze_content(provider, state["source_content"])
    return {
        "analysis": analysis,
        "current_step": "generate",
    }


def _generate_node(state: RepurposeState, provider: LLMProvider) -> dict:
    generated_content: dict[str, str] = {}
    errors = list(state.get("errors", []))
    for fmt in state.get("requested_formats", []):
        generator = GENERATORS.get(fmt)
        if generator is None:
            errors.append(f"Unknown format: {fmt}")
            continue
        generated_content[fmt] = generator(
            provider,
            state["source_content"],
            state["analysis"],
            state.get("tone", "professional"),
            state.get("custom_instructions", {}).get(fmt, ""),
        )
    return {
        "generated_content": generated_content,
        "errors": errors,
        "current_step": "review",
    }


def _review_node(state: RepurposeState) -> dict:
    quality_scores = {
        fmt: assess_quality(body, fmt)
        for fmt, body in state.get("generated_content", {}).items()
    }
    return {
        "quality_scores": quality_scores,
        "current_step": "done",
    }


def build_repurpose_graph(provider: LLMProvider):
    graph = StateGraph(RepurposeState)
    graph.add_node("analyze", lambda state: _analyze_node(state, provider))
    graph.add_node("generate", lambda state: _generate_node(state, provider))
    graph.add_node("review", _review_node)
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "generate")
    graph.add_edge("generate", "review")
    graph.add_edge("review", END)
    return graph.compile()
