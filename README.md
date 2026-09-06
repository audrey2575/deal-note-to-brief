# deal-note-to-brief

Turns messy, real-world call and diligence notes into a structured one-page
investment brief — and, just as importantly, into an explicit list of what
still isn't known.

```
$ python -m dealbrief.cli notes.txt
# Investment Brief: Acme Robotics
**Date:** Not noted | **Attendees:** Not noted | **How We Met:** Not noted
**Sector:** Industrial automation | **Stage:** Seed | **Ask:** $2M at $10M post
## Executive Summary
Warehouses waste roughly 20% of labor hours on manual sorting of mixed-SKU
pallets... Traction so far: 3 paid pilot customers, $180k ARR, 15% MoM growth...
...
```

Full example: [`examples/sample_output.md`](examples/sample_output.md), generated from
[`tests/fixtures/sample_notes.txt`](tests/fixtures/sample_notes.txt).

There's also a styled, standalone HTML version of the same brief (`--html`)
— same content, but built to actually hand to a partner rather than read in
a terminal, and a `--news` flag that adds a live "Recent News" section on
the company (see "What it does" below for both).

## Why I built this

This is the one project in this portfolio that isn't a hypothetical — it's
scoped directly off a workflow I run several times a week as a VC associate.
After every intro call, the notes look roughly the same: half-labeled,
inconsistent, and captured under time pressure, and then someone (usually
me) has to turn them into a clean one-pager before it goes anywhere near an
investment committee. That rewrite step is pure overhead — it doesn't add
judgment, it just costs time and is exactly the kind of repetitive
structuring work a tool should absorb so a person can spend their attention
on the actual decision.

I'm using this project as a small case study in product thinking, not just
a scripting exercise, so here's the reasoning I'd want a hiring manager to
see, not just the code:

- **The user isn't hypothetical.** It's me, and the "spec" came from
  actually noticing where my own time went, not from imagining a persona.
- **Garbage in, garbage flagged — not garbage out.** The easy version of
  this tool would silently produce a confident-looking brief no matter how
  thin the notes were. I decided early that a brief which hides its own
  gaps is actively dangerous in an IC context, so a `## Gaps To Close
  Before IC` section is a first-class part of the output, not an
  afterthought (see `tests/test_brief.py::test_build_brief_surfaces_gaps_for_sparse_notes`).
  The same principle extends to the news feature below: if a live search
  comes back empty or fails, the brief says so in plain language rather
  than just omitting the section silently.
- **The AI layer is optional by design, not by accident.** Parsing and
  structuring never touch the network. Only the 2-3 sentence executive
  summary calls an LLM, and it falls back to a deterministic, rule-based
  summary with zero configuration — because a tool a partner might use
  between meetings has to work with no setup and no flakiness, and because
  it made the core logic trivially unit-testable (31 tests, all offline, all
  deterministic).
- **The one feature that does touch the open internet is opt-in and
  isolated.** `--news` is the single place in this codebase that makes a
  live HTTP call, and it's built the same way the LLM layer is: a small
  `NewsClient` protocol (`dealbrief/news.py`) with a deterministic offline
  mock (what the test suite runs against, and the default) and a real
  client that a user turns on explicitly. The XML-parsing logic is
  separated from the network call specifically so it can be unit-tested
  against a static fixture with zero flakiness, instead of skipping test
  coverage on that code path entirely just because it happens to touch the
  network somewhere else in the same module.
- **v1 is deliberately narrow.** It reads one notes file and writes one
  brief. It does not try to talk to a CRM, auto-file to a deal pipeline, or
  guess at a recommendation the notes didn't support. Scoping it that
  tightly is what made it shippable in a day instead of a "someday" project.

## What it does

1. **Parse** (`dealbrief/parser.py`) — reads semi-structured notes (`Label:
   value` lines, tolerant of casing and common aliases like `Valuation` /
   `Raise` both mapping to the same `ask` field) and pulls out call metadata
   (Date, Attendees, How We Met) plus the deal content itself: Company,
   Sector, Stage, Ask, Problem, Solution, Traction, Team, and Risks. A
   field's value can span multiple lines; a blank line ends it. Anything
   the parser can't find is marked missing explicitly rather than dropped
   silently — the call-metadata fields get a friendlier "Not noted" instead
   of the "follow up on next call" language, since a missing date isn't a
   diligence gap.
2. **Brief** (`dealbrief/brief.py`) — assembles the parsed fields into a
   Markdown one-pager: Date / Attendees / How We Met at the top, a generated
   executive summary, the core sections, a "Gaps To Close Before IC"
   section if anything important is missing, and an optional "Recent News"
   section if a news search was run.
3. **HTML brief** (`dealbrief/html_brief.py`) — the same content rendered as
   a styled, self-contained HTML page (inline CSS, no external assets, no
   build step) — meant to be opened in a browser or emailed as an
   attachment rather than read as plain text.
4. **News lookup** (`dealbrief/news.py`) — an opt-in, on-demand web search
   for recent news about the company, via Google News' public RSS search
   (no API key needed). Off by default; add `--news` to turn it on.
5. **CLI** (`dealbrief/cli.py`) —
   `python -m dealbrief.cli notes.txt [--out brief.md] [--use-claude]
   [--html] [--news] [--news-limit N]`.

## What's next (if this were a real v2)

- A short interactive mode that asks the user the missing-field questions
  directly, instead of just flagging them, so the follow-up call has a
  ready-made checklist.
- A structured JSON export alongside the Markdown, so the same parsed
  fields could feed a lightweight pipeline tracker rather than living only
  as prose.
- Batch mode over a folder of notes, with a rollup view across deals — the
  natural next question once you've used this on a few calls is "how does
  this one compare to the others I've seen this month."
- A hosted, no-install version (upload notes, get a brief back) for anyone
  who'd rather not run a CLI at all.

## Setup

```bash
pip install -r requirements.txt
```

Runs fully offline out of the box. To turn on the Claude-generated
executive summary instead of the rule-based one, set `ANTHROPIC_API_KEY`
and pass `--use-claude`. To turn on the live news search, pass `--news` (no
API key needed — it just needs normal internet access).

## Tests

```bash
PYTHONPATH=. pytest -q
```

31 tests, all passing, all offline. The executive-summary tests use a
deterministic mock LLM client (`dealbrief/llm_client.py`), and the news
tests use a deterministic mock news client plus a static RSS fixture
(`dealbrief/news.py`, `tests/fixtures/google_news_sample.xml`) — so nothing
here depends on a live API key or live network access. The one code path
that does make a real network call (`RealNewsClient.search`) is
intentionally not exercised by the test suite for that reason; it's a thin
wrapper around the `_parse_rss` function that is tested directly.

## Project structure

```
deal-note-to-brief/
├── dealbrief/
│   ├── parser.py       # raw notes -> structured fields
│   ├── brief.py        # structured fields -> Markdown brief
│   ├── html_brief.py    # structured fields -> styled HTML brief
│   ├── news.py          # opt-in live "Recent News" lookup
│   ├── llm_client.py   # Mock (offline/test) + real Claude client
│   └── cli.py          # command-line entry point
├── tests/
│   ├── fixtures/       # sample raw notes + a static news RSS fixture
│   ├── test_parser.py
│   ├── test_brief.py
│   ├── test_html_brief.py
│   ├── test_news.py
│   └── test_cli.py
└── examples/
    └── sample_output.md
```
