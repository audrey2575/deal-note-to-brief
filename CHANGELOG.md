# Changelog

This file exists so the evolution of the project is visible without having
to dig through commit diffs — what changed, and just as importantly, why.

## v0.2.0 — 2026-09-06

**Added:**
- Call metadata at the top of every brief: `Date`, `Attendees`, and `How We
  Met` are now recognized fields (`dealbrief/parser.py`), shown before the
  deal content instead of buried in free-form notes. They're optional —
  older notes without them just show "Not noted" — because a missing call
  date isn't a diligence gap the way a missing Traction figure is.
- A styled, standalone HTML brief (`dealbrief/html_brief.py`, `--html`
  flag). Same content as the Markdown version, but meant to actually be
  opened in a browser or handed to a partner, not read as plain text.
- An opt-in live "Recent News" search on the company (`dealbrief/news.py`,
  `--news` flag), via Google News' public RSS feed — no API key required.
  Built with the same Mock/Real client split as the LLM layer: off by
  default, deterministic in tests, and honest in the output when a search
  comes up empty or fails rather than silently hiding the section.

**Why:** v0.1 answered "can this turn messy notes into a clean brief."
Using it a few times surfaced two gaps: a Markdown file isn't something
you'd actually hand to a partner, and a brief that only reflects one call's
notes misses obvious public context (a funding round, a lawsuit, a product
launch) that changes how you read the rest of the diligence. Both were
real product decisions, not just "add more features" — in particular, the
news section had to be designed to fail loudly rather than fabricate
results, which is the same principle the parser already applied to missing
deal fields.

**Tests:** 12 → 31, all still offline and deterministic.

## v0.1.0 — 2026-09-04

**Added:**
- Tolerant parser for semi-structured call notes (`dealbrief/parser.py`):
  recognizes `Label: value` lines, common aliases (`Valuation`/`Raise`/`Ask`
  all map to one field), multi-line values, and explicitly flags anything
  it couldn't find instead of dropping it.
- Markdown brief generation (`dealbrief/brief.py`) with a generated
  executive summary and a "Gaps To Close Before IC" section.
- Swappable LLM layer (`dealbrief/llm_client.py`): a deterministic mock by
  default (no API key, no network, no flakiness), a real Claude client
  behind `--use-claude`.
- CLI entry point, test suite (12 tests), README, MIT license.
