"""Extract structured fields out of messy, semi-structured deal notes.

The core product bet here: most investors already half-structure their notes
with ad-hoc labels (`Company:`, `Traction:`, `Ask:` ...) but never in a
consistent order, casing, or set of headers. Rather than forcing a rigid
template, this parser is tolerant: it recognizes a known set of labels
(plus common aliases), lets a field's value span multiple lines until the
next recognized label appears, and explicitly flags anything it could not
find rather than silently dropping it. A "brief" that hides its own gaps is
worse than useless for a follow-up call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Canonical field name -> accepted aliases seen in the label position.
LABEL_ALIASES: dict[str, list[str]] = {
    "company": ["company", "company name", "startup"],
    "sector": ["sector", "industry", "vertical"],
    "stage": ["stage", "round"],
    "ask": ["ask", "raise", "valuation", "terms"],
    "problem": ["problem", "problem statement", "pain point"],
    "solution": ["solution", "product"],
    "traction": ["traction", "metrics", "kpis"],
    "team": ["team", "founders", "founding team"],
    "risks": ["risks", "concerns", "open questions", "risk"],
    "notes": ["notes", "follow up", "follow-up", "misc"],
}

# Flattened alias -> canonical lookup, built once at import time.
_ALIAS_TO_FIELD: dict[str, str] = {
    alias: canonical
    for canonical, aliases in LABEL_ALIASES.items()
    for alias in aliases
}

_LABEL_LINE_RE = re.compile(r"^\s*([A-Za-z][A-Za-z \-]{1,25}?)\s*:\s*(.*)$")

REQUIRED_FIELDS = ["company", "sector", "stage", "ask", "problem", "solution", "traction", "team"]
MISSING_PLACEHOLDER = "Not captured — follow up on next call."


@dataclass
class DealNotes:
    """Structured view of a raw notes blob. Missing fields are explicit, not absent."""

    fields: dict[str, str] = field(default_factory=dict)
    raw: str = ""

    def get(self, name: str) -> str:
        return self.fields.get(name, MISSING_PLACEHOLDER)

    def missing_fields(self) -> list[str]:
        return [f for f in REQUIRED_FIELDS if not self.fields.get(f)]


def parse_notes(raw_text: str) -> DealNotes:
    """Parse raw call/diligence notes into a DealNotes object.

    Recognizes a labeled line (``Label: value``) where the label matches one
    of the known aliases above (case-insensitive). Everything after a
    recognized label, up to the next recognized label, is folded into that
    field's value. Text before the first recognized label is ignored (it's
    usually a date/attendee header, not content) rather than raising, since
    real notes are never perfectly formed.
    """
    lines = raw_text.splitlines()
    fields_out: dict[str, list[str]] = {}
    current: str | None = None

    for line in lines:
        match = _LABEL_LINE_RE.match(line)
        canonical = None
        rest = ""
        if match:
            label_candidate = match.group(1).strip().lower()
            canonical = _ALIAS_TO_FIELD.get(label_candidate)
            rest = match.group(2).strip()

        if canonical:
            current = canonical
            fields_out.setdefault(current, [])
            if rest:
                fields_out[current].append(rest)
        elif current and line.strip():
            fields_out[current].append(line.strip())
        elif not line.strip():
            # A blank line ends the current field's span. Without this, a
            # stray unlabeled paragraph later in the notes (common — a
            # closing aside, a scheduling note) would silently glue itself
            # onto whatever field happened to be last, which is worse than
            # dropping it.
            current = None
        # else: stray content before any recognized label — dropped on purpose.

    joined = {k: " ".join(v).strip() for k, v in fields_out.items() if " ".join(v).strip()}
    return DealNotes(fields=joined, raw=raw_text)
