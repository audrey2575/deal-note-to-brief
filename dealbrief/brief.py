"""Assemble a structured DealNotes object into a one-page Markdown brief."""

from __future__ import annotations

from .llm_client import LLMClient, MockLLMClient
from .news import NewsResult
from .parser import HEADER_FIELDS, HEADER_MISSING_PLACEHOLDER, DealNotes


def _prompt_for_summary(notes: DealNotes) -> str:
    return "\n".join(
        f"{name.capitalize()}: {notes.get(name)}"
        for name in ["company", "sector", "stage", "ask", "problem", "solution", "traction", "team"]
    )


def _news_section_lines(news: NewsResult) -> list[str]:
    lines = ["## Recent News"]
    if news.items:
        for item in news.items:
            byline = f" — {item.source}" if item.source else ""
            if item.link:
                lines.append(f"- [{item.title}]({item.link}){byline}")
            else:
                lines.append(f"- {item.title}{byline}")
        if news.error:
            lines.append(f"\n_{news.error}_")
    else:
        lines.append(f"_{news.error or 'No news items found.'}_")
    lines.append("")
    return lines


def build_brief(
    notes: DealNotes,
    llm_client: LLMClient | None = None,
    news: NewsResult | None = None,
) -> str:
    """Render a one-page Markdown investment brief from parsed deal notes.

    ``llm_client`` defaults to the deterministic mock so this is safe (and
    fast, and free) to call in tests or with no API key configured; pass a
    real ``ClaudeClient`` for production use. ``news``, if provided, adds a
    "Recent News" section pulled from a live web search (see ``news.py``) —
    entirely optional, and omitted from the brief if not passed.
    """
    client = llm_client or MockLLMClient()
    company = notes.get("company")

    lines: list[str] = []
    lines.append(f"# Investment Brief: {company}")
    lines.append("")

    header_bits = [
        f"**{label}:** {notes.get(field_name, HEADER_MISSING_PLACEHOLDER)}"
        for field_name, label in HEADER_FIELDS
    ]
    lines.append("  |  ".join(header_bits))
    lines.append(
        f"**Sector:** {notes.get('sector')}  |  **Stage:** {notes.get('stage')}  |  **Ask:** {notes.get('ask')}"
    )
    lines.append("")

    summary = client.summarize(_prompt_for_summary(notes))
    lines.append("## Executive Summary")
    lines.append(summary)
    lines.append("")

    for heading, field_name in [
        ("Problem", "problem"),
        ("Solution", "solution"),
        ("Traction", "traction"),
        ("Team", "team"),
        ("Risks & Open Questions", "risks"),
    ]:
        lines.append(f"## {heading}")
        lines.append(notes.get(field_name))
        lines.append("")

    missing = notes.missing_fields()
    if missing:
        lines.append("## Gaps To Close Before IC")
        for m in missing:
            lines.append(f"- **{m.capitalize()}** was not captured in these notes — follow up before writeup goes to IC.")
        lines.append("")

    extra_notes = notes.fields.get("notes")
    if extra_notes:
        lines.append("## Follow-Up Notes")
        lines.append(extra_notes)
        lines.append("")

    if news is not None:
        lines.extend(_news_section_lines(news))

    return "\n".join(lines).rstrip() + "\n"
