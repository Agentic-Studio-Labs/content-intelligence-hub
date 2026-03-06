import json
from unittest.mock import MagicMock, patch
from agents.query_agent import extract_filters, discover_content


def test_extract_filters_basic():
    provider = MagicMock()
    provider.complete.return_value = json.dumps({
        "search_terms": "cloud migration",
        "filters": {"content_type": "blog", "persona": "cto"},
    })
    result = extract_filters(provider, "Find blog posts about cloud migration for CTOs")
    assert result["search_terms"] == "cloud migration"
    assert result["filters"]["content_type"] == "blog"
    assert result["filters"]["persona"] == "cto"


def test_extract_filters_no_filters():
    provider = MagicMock()
    provider.complete.return_value = json.dumps({
        "search_terms": "devops best practices",
        "filters": {},
    })
    result = extract_filters(provider, "tell me about devops best practices")
    assert result["search_terms"] == "devops best practices"
    assert result["filters"] == {}


@patch("agents.query_agent.hybrid_search")
@patch("agents.query_agent.keyword_search")
def test_discover_content(mock_keyword, mock_hybrid):
    mock_keyword.return_value = [
        {"id": "1", "title": "Cloud Guide", "body": "Content...", "summary": "Summary", "score": 0.9}
    ]
    mock_hybrid.return_value = mock_keyword.return_value

    provider = MagicMock()
    provider.complete.side_effect = [
        json.dumps({"search_terms": "cloud", "filters": {}}),
        "Based on the results, here's what I found about cloud migration...",
    ]
    mock_conn = MagicMock()
    mock_embed = MagicMock()
    mock_embed.embed_text.return_value = [0.1] * 384

    result = discover_content(
        conn=mock_conn,
        provider=provider,
        embedding_model=mock_embed,
        query="tell me about cloud",
    )
    assert "answer" in result
    assert "results" in result
    assert len(result["results"]) > 0
