import json
import logging
from typing import Any

from providers.base import LLMProvider, Message
from search import hybrid_search, keyword_search
from embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


FILTER_EXTRACTION_PROMPT = """Extract search parameters from the user's query.

Return a JSON object with:
- "search_terms": the core search keywords (string)
- "filters": an object with optional keys:
  - "content_type": one of [blog, case_study, email, social_post, landing_page, whitepaper] or null
  - "persona": one of [cto, cfo, developer, marketing_leader, engineer, ceo, cmo] or null
  - "funnel_stage": one of [awareness, consideration, decision, retention] or null
  - "performance_score_gte": minimum performance score (number) or null

Only include filter keys when the user explicitly mentions them or clearly implies them.

<examples>
Query: "Find blog posts about kubernetes for CTOs"
{{"search_terms": "kubernetes", "filters": {{"content_type": "blog", "persona": "cto"}}}}

Query: "high performing content about AI"
{{"search_terms": "AI", "filters": {{"performance_score_gte": 70}}}}

Query: "tell me about cloud migration"
{{"search_terms": "cloud migration", "filters": {{}}}}
</examples>

User query: {query}

Respond with ONLY the JSON object, no other text."""


ANSWER_PROMPT = """Based on the search results below, provide a concise natural language answer to the user's query.

<query>{query}</query>

<results>
{results_text}
</results>

Summarize the key findings. Reference specific content by title. Be concise (2-4 sentences)."""


def extract_filters(provider: LLMProvider, query: str) -> dict:
    prompt = FILTER_EXTRACTION_PROMPT.format(query=query)
    response = provider.complete(
        messages=[Message(role="user", content=prompt)],
        system="You extract structured search parameters from natural language. Respond with JSON only.",
        temperature=0.0,
        max_tokens=256,
    )
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse filter response: {response}")
        return {"search_terms": query, "filters": {}}


def _format_results_for_answer(results: list[dict], limit: int = 5) -> str:
    lines = []
    for i, r in enumerate(results[:limit], 1):
        lines.append(f"{i}. **{r.get('title', 'Untitled')}** ({r.get('content_type', '')})")
        if r.get("summary"):
            lines.append(f"   {r['summary'][:200]}")
        lines.append("")
    return "\n".join(lines)


def discover_content(
    conn,
    provider: LLMProvider,
    embedding_model: EmbeddingModel,
    query: str,
) -> dict[str, Any]:
    extracted = extract_filters(provider, query)
    search_terms = extracted.get("search_terms", query)
    filters = extracted.get("filters", {})
    query_embedding = embedding_model.embed_text(search_terms)
    results = hybrid_search(
        conn, search_terms, query_embedding, filters=filters, limit=10
    )
    if not results:
        results = keyword_search(conn, search_terms, filters=filters, limit=10)
    results_text = _format_results_for_answer(results)
    answer_prompt = ANSWER_PROMPT.format(query=query, results_text=results_text)
    answer = provider.complete(
        messages=[Message(role="user", content=answer_prompt)],
        system="You are a helpful content discovery assistant. Be concise and specific.",
        temperature=0.3,
    )
    return {
        "query": query,
        "answer": answer,
        "results": results,
        "filters_applied": filters,
        "search_terms": search_terms,
    }
