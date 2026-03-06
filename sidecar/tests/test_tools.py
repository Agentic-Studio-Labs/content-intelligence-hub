from unittest.mock import MagicMock
from agents.tools import (
    analyze_content,
    generate_linkedin_post,
    generate_email,
    generate_twitter_thread,
    generate_summary,
    assess_quality,
)


def _make_mock_provider(response_text: str) -> MagicMock:
    provider = MagicMock()
    provider.complete.return_value = response_text
    return provider


MOCK_ANALYSIS = """## Key Themes
Cloud migration strategy, digital transformation

## Target Audience
CTOs and engineering leaders

## Tone & Voice
Professional, authoritative

## Value Proposition
Comprehensive roadmap reduces migration risk

## Call to Action
Download the migration checklist

## Key Stats/Facts
85% of enterprises plan cloud migration by 2026"""


def test_analyze_content():
    provider = _make_mock_provider(MOCK_ANALYSIS)
    source = {"title": "Cloud Migration Guide", "body": "Cloud migration content...", "summary": "A guide."}
    result = analyze_content(provider, source)
    assert "themes" in result
    assert "audience" in result
    assert "tone" in result
    provider.complete.assert_called_once()


def test_generate_linkedin_post():
    provider = _make_mock_provider("Exciting news about cloud migration!\n\nKey insight here.\n\n#Cloud #Migration")
    source = {"title": "Cloud Guide", "body": "Content...", "summary": "Summary."}
    analysis = {"themes": "cloud", "audience": "CTOs", "tone": "professional"}
    result = generate_linkedin_post(provider, source, analysis, tone="professional")
    assert len(result) > 0
    provider.complete.assert_called_once()


def test_generate_email():
    provider = _make_mock_provider("Subject: Cloud Migration Insights\n\nDear Leader,\n\nBody here.")
    source = {"title": "Cloud Guide", "body": "Content...", "summary": "Summary."}
    analysis = {"themes": "cloud", "audience": "CTOs", "tone": "professional"}
    result = generate_email(provider, source, analysis, tone="professional")
    assert len(result) > 0


def test_generate_twitter_thread():
    provider = _make_mock_provider("1/5 Cloud migration is transforming...\n\n2/5 Key insight...")
    source = {"title": "Cloud Guide", "body": "Content...", "summary": "Summary."}
    analysis = {"themes": "cloud", "audience": "CTOs", "tone": "professional"}
    result = generate_twitter_thread(provider, source, analysis, tone="casual")
    assert len(result) > 0


def test_generate_summary():
    provider = _make_mock_provider("- Key insight about cloud migration\n- Second point\n- Third point")
    source = {"title": "Cloud Guide", "body": "Content...", "summary": "Summary."}
    analysis = {"themes": "cloud", "audience": "CTOs", "tone": "professional"}
    result = generate_summary(provider, source, analysis, tone="professional")
    assert len(result) > 0


def test_assess_quality_good_content():
    score = assess_quality(
        generated_content="This is a well-written LinkedIn post about cloud migration. "
        "It covers key themes and includes a clear call to action. " * 5,
        format_type="linkedin",
    )
    assert 0.0 <= score <= 1.0
    assert score >= 0.5


def test_assess_quality_too_short():
    score = assess_quality(generated_content="Short.", format_type="linkedin")
    assert score < 0.5


def test_assess_quality_no_cta():
    score = assess_quality(
        generated_content="This is a LinkedIn post about cloud migration. " * 5,
        format_type="linkedin",
    )
    assert score < 1.0
