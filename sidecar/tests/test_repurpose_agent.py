from unittest.mock import MagicMock, patch
from agents.state import RepurposeState
from agents.repurpose_agent import build_repurpose_graph, repurpose_content


def test_repurpose_state_has_required_fields():
    state = RepurposeState(
        messages=[],
        source_content_id="test-id",
        requested_formats=["linkedin"],
        tone="professional",
    )
    assert state["source_content_id"] == "test-id"
    assert state["requested_formats"] == ["linkedin"]


@patch("agents.repurpose_agent.get_content_by_id")
@patch("agents.repurpose_agent.get_similar_content")
def test_repurpose_content_end_to_end(mock_similar, mock_get_content):
    mock_get_content.return_value = {
        "id": "test-id",
        "title": "Cloud Guide",
        "body": "Cloud migration content here." * 10,
        "summary": "A guide to cloud.",
    }
    mock_similar.return_value = []

    mock_provider = MagicMock()
    mock_provider.complete.side_effect = [
        # analyze_content response
        "## Key Themes\ncloud\n## Target Audience\nCTOs\n## Tone & Voice\nprofessional\n## Value Proposition\nvalue\n## Call to Action\nlearn more\n## Key Stats/Facts\nnone",
        # generate_linkedin_post response
        "Great LinkedIn post about cloud. Learn more at our site. #Cloud",
    ]

    mock_conn = MagicMock()
    result = repurpose_content(
        conn=mock_conn,
        provider=mock_provider,
        content_id="test-id",
        formats=["linkedin"],
        tone="professional",
    )
    assert result["success"] is True
    assert "linkedin" in result["generated_content"]
    assert "linkedin" in result["quality_scores"]


@patch("agents.repurpose_agent.get_content_by_id")
def test_repurpose_content_not_found(mock_get_content):
    mock_get_content.return_value = None
    mock_conn = MagicMock()
    mock_provider = MagicMock()
    result = repurpose_content(
        conn=mock_conn,
        provider=mock_provider,
        content_id="nonexistent",
        formats=["linkedin"],
    )
    assert result["success"] is False
    assert len(result["errors"]) > 0
