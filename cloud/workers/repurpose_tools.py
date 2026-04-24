import re

from shared.providers.base import LLMProvider, Message


ANALYSIS_PROMPT = """Analyze the following marketing content and extract structured information.

<content>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</content>

Respond with these sections using ## headers:

## Key Themes
Main topics and themes (comma-separated)

## Target Audience
Who this content is for

## Tone & Voice
The writing style and tone

## Value Proposition
The core value being communicated

## Call to Action
The desired next step for the reader

## Key Stats/Facts
Any notable statistics or facts mentioned"""


LINKEDIN_PROMPT = """Create a LinkedIn post based on this source content.

<source>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</source>

<analysis>{analysis}</analysis>

<instructions>
Tone: {tone}
{custom_instructions}
</instructions>

Write a ~300 word LinkedIn post with:
1. An attention-grabbing hook (first line)
2. 2-3 paragraphs of insight
3. A key takeaway
4. A call to action
5. 3-5 relevant hashtags

Do NOT include a title or "LinkedIn Post:" prefix. Just write the post directly."""


EMAIL_PROMPT = """Create a marketing email based on this source content.

<source>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</source>

<analysis>{analysis}</analysis>

<instructions>
Tone: {tone}
{custom_instructions}
</instructions>

Write an email with:
- Subject line (under 50 characters)
- Preview text (first 50 characters that appear in inbox)
- Personalized opener
- Value proposition (2-3 sentences)
- Social proof or key stat
- Clear CTA
- Professional signature placeholder

Format as:
Subject: ...
Preview: ...

[email body]"""


TWITTER_PROMPT = """Create a Twitter/X thread based on this source content.

<source>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</source>

<analysis>{analysis}</analysis>

<instructions>
Tone: {tone}
{custom_instructions}
</instructions>

Write a 5-7 tweet thread. Number each tweet (1/N format). Each tweet MUST be under 280 characters.

Structure:
1. Hook tweet with main insight
2. Context/background
3-5. Key points with specifics
6. Summary + CTA
7. Engagement ask"""


SUMMARY_PROMPT = """Create an executive summary of this content.

<source>
<title>{title}</title>
<summary>{summary}</summary>
<body>{body}</body>
</source>

<analysis>{analysis}</analysis>

<instructions>
Tone: {tone}
{custom_instructions}
</instructions>

Write 3-5 actionable bullet points covering:
- Most important insights
- Actionable items
- Key benefits or outcomes

Use "- " prefix for each bullet. Be concise and specific."""


def analyze_content(provider: LLMProvider, source_content: dict) -> dict:
    response = provider.complete(
        messages=[
            Message(
                role="user",
                content=ANALYSIS_PROMPT.format(
                    title=source_content.get("title", ""),
                    summary=source_content.get("summary", ""),
                    body=source_content.get("body", ""),
                ),
            )
        ],
        system="You are a marketing content analyst. Extract structured information accurately.",
        temperature=0.3,
    )
    return parse_analysis(response)


def parse_analysis(text: str) -> dict:
    sections = {
        "themes": "Key Themes",
        "audience": "Target Audience",
        "tone": "Tone & Voice",
        "value_prop": "Value Proposition",
        "cta": "Call to Action",
        "key_facts": "Key Stats/Facts",
    }
    result = {"raw_analysis": text}
    for key, header in sections.items():
        pattern = rf"##\s*{re.escape(header)}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        result[key] = match.group(1).strip() if match else ""
    return result


def format_analysis(analysis: dict) -> str:
    parts = []
    for key in ("themes", "audience", "tone", "value_prop", "cta", "key_facts"):
        if analysis.get(key):
            parts.append(f"{key}: {analysis[key]}")
    return "\n".join(parts)


def generate(provider: LLMProvider, prompt: str, *, system: str) -> str:
    return provider.complete(
        messages=[Message(role="user", content=prompt)],
        system=system,
        temperature=0.7,
    )


def generate_linkedin_post(
    provider: LLMProvider,
    source_content: dict,
    analysis: dict,
    tone: str,
    custom_instructions: str,
) -> str:
    return generate(
        provider,
        LINKEDIN_PROMPT.format(
            title=source_content.get("title", ""),
            summary=source_content.get("summary", ""),
            body=source_content.get("body", ""),
            analysis=format_analysis(analysis),
            tone=tone,
            custom_instructions=custom_instructions,
        ),
        system="You are an expert LinkedIn content creator.",
    )


def generate_email(
    provider: LLMProvider,
    source_content: dict,
    analysis: dict,
    tone: str,
    custom_instructions: str,
) -> str:
    return generate(
        provider,
        EMAIL_PROMPT.format(
            title=source_content.get("title", ""),
            summary=source_content.get("summary", ""),
            body=source_content.get("body", ""),
            analysis=format_analysis(analysis),
            tone=tone,
            custom_instructions=custom_instructions,
        ),
        system="You are an expert email marketing copywriter.",
    )


def generate_twitter_thread(
    provider: LLMProvider,
    source_content: dict,
    analysis: dict,
    tone: str,
    custom_instructions: str,
) -> str:
    return generate(
        provider,
        TWITTER_PROMPT.format(
            title=source_content.get("title", ""),
            summary=source_content.get("summary", ""),
            body=source_content.get("body", ""),
            analysis=format_analysis(analysis),
            tone=tone,
            custom_instructions=custom_instructions,
        ),
        system="You are an expert Twitter/X content creator.",
    )


def generate_summary(
    provider: LLMProvider,
    source_content: dict,
    analysis: dict,
    tone: str,
    custom_instructions: str,
) -> str:
    return provider.complete(
        messages=[
            Message(
                role="user",
                content=SUMMARY_PROMPT.format(
                    title=source_content.get("title", ""),
                    summary=source_content.get("summary", ""),
                    body=source_content.get("body", ""),
                    analysis=format_analysis(analysis),
                    tone=tone,
                    custom_instructions=custom_instructions,
                ),
            )
        ],
        system="You are an expert content strategist.",
        temperature=0.3,
    )


GENERATORS = {
    "linkedin": generate_linkedin_post,
    "email": generate_email,
    "twitter": generate_twitter_thread,
    "summary": generate_summary,
}


def assess_quality(generated_content: str, format_type: str) -> float:
    score = 1.0
    if len(generated_content) < 100:
        score -= 0.5
    if format_type != "summary":
        cta_patterns = r"(learn more|check out|click|sign up|download|register|visit|get started|try|join)"
        if not re.search(cta_patterns, generated_content, re.IGNORECASE):
            score -= 0.1
    return max(0.0, min(1.0, score))
