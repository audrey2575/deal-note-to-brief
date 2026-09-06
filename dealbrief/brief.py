"""Assemble a structured DealNotes object into a one-page Markdown brief."""

from __future__ import annotations

from .llm_client import LLMClient, MockLLMClient
from .parser import DealNotes


def _prompt_for_summary(notes: DealNotes) -> str:
    return "\n".join(
        f"{name.capitalize()}: {notes.get(name)}"
        for name in ["company", "sector", "stage", "ask", "problem", "solution", "traction", "team"]
    )


def build_brief(notes: DealNotes, llm_client: LLMClient | None = None) -> str:
    """Render a one-page Markdown investment brief from parsed deal notes.

    ``llm_client`` defaults to the deterministic mock so this is safe (and
    fast, and free) to call in tests or with no API key configured; pass a
    real ``ClaudeClient`` for production use.
    """
    client = llm_client or MockLLMClient()
    company = notes.get("company")

    lines: list[str] = []
    lines.append(f"# Investment Brief: {company}")
    lines.append("")
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

    return "\n".join(lines).rstrip() + "\n"
