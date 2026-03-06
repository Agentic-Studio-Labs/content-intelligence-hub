import logging
from typing import Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from agents.state import RepurposeState
from agents.tools import analyze_content, assess_quality, GENERATE_FN
from db import get_content_by_id
from search import get_similar_content
from providers.base import LLMProvider

logger = logging.getLogger(__name__)


def _fetch_source_node(state: RepurposeState, conn, provider) -> dict:
    content_id = state["source_content_id"]
    content = get_content_by_id(conn, content_id)
    if not content:
        return {
            "errors": state.get("errors", []) + [f"Content {content_id} not found"],
            "current_step": "error",
        }
    similar = get_similar_content(conn, content_id, limit=3)
    return {
        "source_content": content,
        "similar_content": similar,
        "current_step": "analyze",
        "messages": [HumanMessage(content=f"Fetched source: {content['title']}")],
    }


def _analyze_node(state: RepurposeState, conn, provider) -> dict:
    source = state.get("source_content")
    if not source:
        return {"errors": state.get("errors", []) + ["No source content to analyze"]}
    analysis = analyze_content(provider, source)
    return {
        "content_analysis": analysis,
        "current_step": "generate",
        "messages": [HumanMessage(content=f"Analysis complete: {analysis.get('themes', '')}")],
    }


def _generate_node(state: RepurposeState, conn, provider) -> dict:
    source = state.get("source_content", {})
    analysis = state.get("content_analysis", {})
    tone = state.get("tone", "professional")
    custom = state.get("custom_instructions", {})
    formats = state.get("requested_formats", [])
    generated = {}
    errors = list(state.get("errors", []))
    for fmt in formats:
        gen_fn = GENERATE_FN.get(fmt)
        if not gen_fn:
            errors.append(f"Unknown format: {fmt}")
            continue
        try:
            result = gen_fn(
                provider, source, analysis,
                tone=tone,
                custom_instructions=custom.get(fmt, ""),
            )
            generated[fmt] = result
        except Exception as e:
            errors.append(f"Error generating {fmt}: {e}")
            logger.exception(f"Generation error for {fmt}")
    return {
        "generated_content": generated,
        "errors": errors,
        "current_step": "review",
    }


def _review_node(state: RepurposeState, conn, provider) -> dict:
    generated = state.get("generated_content", {})
    source = state.get("source_content")
    scores = {}
    for fmt, content in generated.items():
        scores[fmt] = assess_quality(content, fmt, source)
        logger.info(f"Quality score for {fmt}: {scores[fmt]:.2f}")
    return {
        "quality_scores": scores,
        "current_step": "done",
    }


def build_repurpose_graph(conn, provider: LLMProvider) -> StateGraph:
    graph = StateGraph(RepurposeState)
    graph.add_node("fetch_source", lambda s: _fetch_source_node(s, conn, provider))
    graph.add_node("analyze", lambda s: _analyze_node(s, conn, provider))
    graph.add_node("generate", lambda s: _generate_node(s, conn, provider))
    graph.add_node("review", lambda s: _review_node(s, conn, provider))
    graph.set_entry_point("fetch_source")

    def route_after_fetch(state):
        if state.get("current_step") == "error":
            return END
        return "analyze"

    graph.add_conditional_edges("fetch_source", route_after_fetch, {"analyze": "analyze", END: END})
    graph.add_edge("analyze", "generate")
    graph.add_edge("generate", "review")
    graph.add_edge("review", END)
    return graph.compile()


def repurpose_content(
    conn,
    provider: LLMProvider,
    content_id: str,
    formats: list[str],
    tone: str = "professional",
    custom_instructions: dict[str, str] | None = None,
) -> dict[str, Any]:
    app = build_repurpose_graph(conn, provider)
    initial_state: RepurposeState = {
        "messages": [],
        "source_content_id": content_id,
        "requested_formats": formats,
        "tone": tone,
        "custom_instructions": custom_instructions or {},
        "errors": [],
        "generated_content": {},
        "quality_scores": {},
    }
    try:
        final_state = app.invoke(initial_state)
    except Exception as e:
        return {"success": False, "errors": [str(e)], "generated_content": {}, "quality_scores": {}}
    errors = final_state.get("errors", [])
    generated = final_state.get("generated_content", {})
    return {
        "success": len(generated) > 0,
        "generated_content": generated,
        "quality_scores": final_state.get("quality_scores", {}),
        "analysis": final_state.get("content_analysis", {}),
        "errors": errors,
    }
