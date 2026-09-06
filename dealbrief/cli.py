"""Command-line entry point: notes in, brief out.

    python -m dealbrief.cli notes.txt                 # prints brief to stdout
    python -m dealbrief.cli notes.txt --out brief.md   # writes to a file
    python -m dealbrief.cli notes.txt --use-claude     # adds a Claude-written
                                                        # executive summary
                                                        # (requires ANTHROPIC_API_KEY)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .brief import build_brief
from .llm_client import ClaudeClient, MockLLMClient
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
    args = parser.parse_args(argv)

    raw_text = Path(args.notes_file).read_text()
    notes = parse_notes(raw_text)

    client = ClaudeClient() if args.use_claude else MockLLMClient()
    brief_text = build_brief(notes, llm_client=client)

    if args.out:
        Path(args.out).write_text(brief_text)
        print(f"Wrote brief to {args.out}")
    else:
        print(brief_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
