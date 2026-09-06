"""LLM client abstraction for the optional executive-summary layer.

Product decision worth spelling out: the parser and brief formatter never
*require* an LLM call — a partner should be able to run this on a plane with
no API key and still get a clean, structured brief. The LLM is layered on
top purely to add a 2-3 sentence narrative summary, and it's the one part
that touches the network, so it's the one part that's swappable/mockable.

This mirrors the pattern used in the biolit-explorer and claude-agent-lab
projects in this same portfolio: a small ``LLMClient`` protocol with a
deterministic ``MockLLMClient`` (what the test suite runs against, and what
runs when no API key is configured) and a thin ``ClaudeClient`` wrapper for
real use.
"""

from __future__ import annotations

import os
from typing import Protocol


class LLMClient(Protocol):
    def summarize(self, prompt: str) -> str:
        ...


class MockLLMClient:
    """Deterministic, offline stand-in. No network calls, ever."""

    def summarize(self, prompt: str) -> str:
        # Deliberately simple and deterministic so tests never flake and the
        # tool degrades gracefully with no API key: it pulls the first
        # sentence-like chunk out of the prompt's "Problem" and "Traction"
        # sections rather than fabricating anything.
        lines = [line for line in prompt.splitlines() if line.strip()]
        problem_line = next((l for l in lines if l.lower().startswith("problem:")), "")
        traction_line = next((l for l in lines if l.lower().startswith("traction:")), "")
        parts = []
        if problem_line:
            parts.append(problem_line.split(":", 1)[1].strip())
        if traction_line:
            parts.append(f"Traction so far: {traction_line.split(':', 1)[1].strip()}")
        if not parts:
            return "Not enough structured detail to summarize automatically — see full notes below."
        return " ".join(parts)


class ClaudeClient:
    """Thin wrapper around the real Anthropic API. Not used in tests."""

    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Export it, or use MockLLMClient for offline use."
            )

    def summarize(self, prompt: str) -> str:
        import anthropic  # imported lazily so the package has zero hard dependency

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Write a tight 2-3 sentence executive summary of this "
                        "investment opportunity for a partner meeting, in a "
                        "neutral analytical tone (not promotional):\n\n" + prompt
                    ),
                }
            ],
        )
        return response.content[0].text.strip()


def get_default_client() -> LLMClient:
    """Return a real Claude client if an API key is configured, else the mock."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ClaudeClient()
    return MockLLMClient()
