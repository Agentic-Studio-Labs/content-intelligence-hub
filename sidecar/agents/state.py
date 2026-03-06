from typing import Any, TypedDict, Annotated
from langgraph.graph.message import add_messages


class RepurposeState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    source_content_id: str
    requested_formats: list[str]
    tone: str
    custom_instructions: dict[str, str]
    source_content: dict[str, Any]
    similar_content: list[dict[str, Any]]
    content_analysis: dict[str, Any]
    generated_content: dict[str, str]
    quality_scores: dict[str, float]
    current_step: str
    errors: list[str]
