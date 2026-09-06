"""Command-line entry point: notes in, brief out.

    python -m dealbrief.cli notes.txt                  # Markdown brief to stdout
    python -m dealbrief.cli notes.txt --out brief.md    # writes Markdown to a file
    python -m dealbrief.cli notes.txt --html --out brief.html
                                                         # styled HTML brief instead
    python -m dealbrief.cli notes.txt --use-claude      # adds a Claude-written
                                                         # executive summary
                                                         # (requires ANTHROPIC_API_KEY)
    python -m dealbrief.cli notes.txt --news            # adds a live "Recent News"
                                                         # section (real internet
                                                         # search, no API key needed)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .brief import build_brief
from .html_brief import render_html_brief
from .llm_client import ClaudeClient, MockLLMClient
from .news import get_default_news_client
from .parser import parse_notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Turn raw deal notes into a structured one-page brief.")
    parser.add_argument("notes_file", type=str, help="Path to a text file of raw notes.")
    parser.add_argument("--out", type=str, default=None, help="Write the brief here instead of stdout.")
    parser.add_argument(
        "--use-claude",
        action="store_true",
        help="Use the real Claude API for the executive summary (requires ANTHROPIC_API_KEY).",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Render a styled, standalone HTML brief instead of Markdown.",
    )
    parser.add_argument(
        "--news",
        action="store_true",
        help=(
            "Fetch a live 'Recent News' section for the company via Google News' "
            "public RSS search (real internet access, no API key required). "
            "Without this flag, the brief is fully offline."
        ),
    )
    parser.add_argument(
        "--news-limit",
        type=int,
        default=5,
        help="Max number of news items to include when --news is passed (default: 5).",
    )
    args = parser.parse_args(argv)

    raw_text = Path(args.notes_file).read_text()
    notes = parse_notes(raw_text)

    client = ClaudeClient() if args.use_claude else MockLLMClient()

    news_result = None
    if args.news:
        company = notes.get("company")
        news_client = get_default_news_client(live=True)
        news_result = news_client.search(company, limit=args.news_limit)
        if not news_result.ok and news_result.error:
            print(f"[news] {news_result.error}", file=sys.stderr)

    if args.html:
        output_text = render_html_brief(notes, llm_client=client, news=news_result)
    else:
        output_text = build_brief(notes, llm_client=client, news=news_result)

    if args.out:
        Path(args.out).write_text(output_text)
        print(f"Wrote brief to {args.out}")
    else:
        print(output_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
