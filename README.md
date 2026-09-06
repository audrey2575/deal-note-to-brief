# deal-note-to-brief

Turns messy, real-world call and diligence notes into a structured one-page
investment brief, and, just as importantly, into an explicit list of what
still isn't known.

```
$ python -m dealbrief.cli notes.txt
# Investment Brief: Acme Robotics
**Sector:** Industrial automation | **Stage:** Seed | **Ask:** $2M at $10M post
## Executive Summary
Warehouses waste roughly 20% of labor hours on manual sorting of mixed-SKU
pallets... Traction so far: 3 paid pilot customers, $180k ARR, 15% MoM growth...
...
```

Full example: [`examples/sample_output.md`](examples/sample_output.md), generated from
[`tests/fixtures/sample_notes.txt`](tests/fixtures/sample_notes.txt).

## Why I built this

This is the one project in this portfolio that isn't a hypothetical. It's
scoped directly off a workflow I run several times a week as a VC associate.
After every intro call, the notes look roughly the same: half-labeled,
inconsistent, and captured under time pressure, and then someone (usually
me) has to turn them into a clean one-pager. That rewrite step is pure overhead, it doesn't add
judgment, it just costs time and is exactly the kind of repetitive
structuring work a tool should absorb so a person can spend their attention
on the actual decision.

I'm using this project as a small case study in product thinking, not just
a scripting exercise.

- **The user isn't hypothetical.** It's me, and the "spec" came from
  actually noticing where my own time went, not from imagining a persona.
- **Garbage in, garbage flagged, not garbage out.** The easy version of
  this tool would silently produce a confident-looking brief no matter how
  thin the notes were. I decided early that a brief which hides its own
  gaps is actively dangerous in an IC context, so a `## Gaps To Close
  Before IC` section is a first-class part of the output, not an
  afterthought (see `tests/test_brief.py::test_build_brief_surfaces_gaps_for_sparse_notes`).
- **The AI layer is optional by design, not by accident.** Parsing and
  structuring never touch the network. Only the 2-3 sentence executive
  summary calls an LLM, and it falls back to a deterministic, rule-based
  summary with zero configuration, because a tool a partner might use
  between meetings has to work with no setup and no flakiness, and because
  it made the core logic trivially unit-testable (12 tests, all offline, all
  deterministic).
- **v1 is deliberately narrow.** It reads one notes file and writes one
  brief. It does not try to talk to a CRM, auto-file to a deal pipeline, or
  guess at a recommendation the notes didn't support. Scoping it that
  tightly is what made it shippable in a day instead of a "someday" project.

## What it does

1. **Parse** (`dealbrief/parser.py`) — reads semi-structured notes (`Label:
   value` lines, tolerant of casing and common aliases like `Valuation` /
   `Raise` both mapping to the same `ask` field) and pulls out Company,
   Sector, Stage, Ask, Problem, Solution, Traction, Team, and Risks. A
   field's value can span multiple lines; a blank line ends it. Anything
   the parser can't find is marked missing explicitly rather than dropped
   silently.
2. **Brief** (`dealbrief/brief.py`) — assembles the parsed fields into a
   Markdown one-pager with a generated executive summary up top, and a
   "Gaps To Close Before IC" section if anything important is missing.
3. **CLI** (`dealbrief/cli.py`) — `python -m dealbrief.cli notes.txt [--out
   brief.md] [--use-claude]`.

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

## Setup

```bash
pip install -r requirements.txt
```

Runs fully offline out of the box. To turn on the Claude-generated
executive summary instead of the rule-based one, set `ANTHROPIC_API_KEY`
and pass `--use-claude`.

## Tests

```bash
PYTHONPATH=. pytest -q
```

12 tests, all passing, all offline (they use a deterministic mock LLM
client — see `dealbrief/llm_client.py` — so nothing here depends on a live
API key or network access).

## Project structure

```
deal-note-to-brief/
├── dealbrief/
│   ├── parser.py       # raw notes -> structured fields
│   ├── brief.py        # structured fields -> Markdown brief
│   ├── llm_client.py   # Mock (offline/test) + real Claude client
│   └── cli.py          # command-line entry point
├── tests/
│   ├── fixtures/       # sample raw notes, well-formed and sparse
│   ├── test_parser.py
│   ├── test_brief.py
│   └── test_cli.py
└── examples/
    └── sample_output.md
```
