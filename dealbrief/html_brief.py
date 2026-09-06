"""Render a DealNotes object as a styled, standalone HTML brief.

Why this exists alongside ``brief.py`` rather than replacing it: the
Markdown brief is the thing meant to be read in a terminal, pasted into
Slack, or diffed in a PR. This HTML version is the one meant to be opened
in a browser and actually look like something you'd hand to a partner —
same underlying content, same "don't hide the gaps" principle, different
audience. No build step, no server, no external assets: the file this
module returns is fully self-contained (inline CSS, no network calls) so it
opens correctly by double-clicking it from Finder/Explorer.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone

from .llm_client import LLMClient, MockLLMClient
from .news import NewsResult
from .parser import HEADER_FIELDS, HEADER_MISSING_PLACEHOLDER, DealNotes
from .brief import _prompt_for_summary

_CSS = """
  :root {
    --ink: #1c2333;
    --muted: #5b6472;
    --line: #e4e7ec;
    --accent: #4f46e5;
    --accent-soft: #eef0fe;
    --warn-bg: #fff7ed;
    --warn-line: #fed7aa;
    --warn-ink: #9a3412;
    --news-bg: #f5f8ff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 2.5rem 1.5rem;
    background: #f4f5f7;
    color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.55;
  }
  .sheet {
    max-width: 760px;
    margin: 0 auto;
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 2.5rem 3rem;
    box-shadow: 0 1px 3px rgba(20, 20, 40, 0.06);
  }
  .eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--accent);
    margin: 0 0 0.35rem 0;
  }
  h1 {
    margin: 0 0 1.1rem 0;
    font-size: 1.75rem;
    letter-spacing: -0.01em;
  }
  .meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.75rem 1.25rem;
    background: var(--accent-soft);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 1.75rem;
  }
  .meta-item .label {
    display: block;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    margin-bottom: 0.15rem;
  }
  .meta-item .value {
    font-size: 0.92rem;
    font-weight: 600;
  }
  section { margin-bottom: 1.6rem; }
  section h2 {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    border-bottom: 1px solid var(--line);
    padding-bottom: 0.4rem;
    margin: 0 0 0.6rem 0;
  }
  section p {
    margin: 0;
    white-space: pre-line;
  }
  .summary {
    background: var(--accent-soft);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    font-size: 1rem;
  }
  .gaps {
    background: var(--warn-bg);
    border: 1px solid var(--warn-line);
    border-radius: 10px;
    padding: 1rem 1.25rem;
  }
  .gaps h2 { color: var(--warn-ink); border-bottom-color: var(--warn-line); }
  .gaps ul { margin: 0; padding-left: 1.1rem; }
  .gaps li { margin-bottom: 0.3rem; }
  .news {
    background: var(--news-bg);
    border-radius: 10px;
    padding: 1rem 1.25rem;
  }
  .news ul { margin: 0.4rem 0 0 0; padding-left: 1.1rem; }
  .news li { margin-bottom: 0.5rem; }
  .news a { color: var(--accent); text-decoration: none; font-weight: 600; }
  .news a:hover { text-decoration: underline; }
  .news .src { color: var(--muted); font-size: 0.82rem; }
  .news .note { color: var(--muted); font-size: 0.85rem; margin-top: 0.5rem; }
  footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--line);
    font-size: 0.75rem;
    color: var(--muted);
  }
"""


def _esc(value: str) -> str:
    return html.escape(value, quote=False)


def _meta_grid(notes: DealNotes) -> str:
    items = list(HEADER_FIELDS) + [("sector", "Sector"), ("stage", "Stage"), ("ask", "Ask")]
    cells = []
    for field_name, label in items:
        default = HEADER_MISSING_PLACEHOLDER if field_name in dict(HEADER_FIELDS) else None
        value = notes.get(field_name, default) if default is not None else notes.get(field_name)
        cells.append(
            f'<div class="meta-item"><span class="label">{_esc(label)}</span>'
            f'<span class="value">{_esc(value)}</span></div>'
        )
    return f'<div class="meta-grid">{"".join(cells)}</div>'


def _news_html(news: NewsResult) -> str:
    parts = ['<section class="news"><h2>Recent News</h2>']
    if news.items:
        parts.append("<ul>")
        for item in news.items:
            title = _esc(item.title)
            link = _esc(item.link)
            source = f' <span class="src">— {_esc(item.source)}</span>' if item.source else ""
            if link:
                parts.append(f'<li><a href="{link}">{title}</a>{source}</li>')
            else:
                parts.append(f"<li>{title}{source}</li>")
        parts.append("</ul>")
        if news.error:
            parts.append(f'<p class="note">{_esc(news.error)}</p>')
    else:
        parts.append(f'<p class="note">{_esc(news.error or "No news items found.")}</p>')
    parts.append("</section>")
    return "".join(parts)


def render_html_brief(
    notes: DealNotes,
    llm_client: LLMClient | None = None,
    news: NewsResult | None = None,
) -> str:
    """Render a one-page, self-contained HTML investment brief.

    Same inputs as ``build_brief`` (Markdown version) — pass the same
    ``DealNotes``, optionally the same ``llm_client`` and ``news`` result,
    to get a styled page instead of a Markdown file. No external
    dependencies: safe to email as an attachment or open by double-click.
    """
    client = llm_client or MockLLMClient()
    company = notes.get("company")
    summary = client.summarize(_prompt_for_summary(notes))
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    body_sections = []
    for heading, field_name in [
        ("Problem", "problem"),
        ("Solution", "solution"),
        ("Traction", "traction"),
        ("Team", "team"),
        ("Risks & Open Questions", "risks"),
    ]:
        body_sections.append(
            f"<section><h2>{_esc(heading)}</h2><p>{_esc(notes.get(field_name))}</p></section>"
        )

    missing = notes.missing_fields()
    gaps_html = ""
    if missing:
        items = "".join(
            f"<li><strong>{_esc(m.capitalize())}</strong> was not captured in these notes"
            " — follow up before writeup goes to IC.</li>"
            for m in missing
        )
        gaps_html = f'<section class="gaps"><h2>Gaps To Close Before IC</h2><ul>{items}</ul></section>'

    extra_notes = notes.fields.get("notes")
    followup_html = ""
    if extra_notes:
        followup_html = f"<section><h2>Follow-Up Notes</h2><p>{_esc(extra_notes)}</p></section>"

    news_html = _news_html(news) if news is not None else ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Investment Brief — {_esc(company)}</title>
<style>{_CSS}</style>
</head>
<body>
  <div class="sheet">
    <p class="eyebrow">Investment Brief</p>
    <h1>{_esc(company)}</h1>
    {_meta_grid(notes)}
    <section class="summary-section">
      <h2>Executive Summary</h2>
      <p class="summary">{_esc(summary)}</p>
    </section>
    {"".join(body_sections)}
    {gaps_html}
    {followup_html}
    {news_html}
    <footer>Generated by deal-note-to-brief on {generated}.</footer>
  </div>
</body>
</html>
"""
