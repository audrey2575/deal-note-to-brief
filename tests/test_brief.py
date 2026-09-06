from pathlib import Path

from dealbrief.brief import build_brief
from dealbrief.llm_client import MockLLMClient
from dealbrief.parser import parse_notes

FIXTURES = Path(__file__).parent / "fixtures"


def test_build_brief_includes_all_core_sections():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    out = build_brief(notes, llm_client=MockLLMClient())

    assert out.startswith("# Investment Brief: Acme Robotics")
    for heading in [
        "## Executive Summary",
        "## Problem",
        "## Solution",
        "## Traction",
        "## Team",
        "## Risks & Open Questions",
        "## Follow-Up Notes",
    ]:
        assert heading in out
    # Nothing was missing in this fixture, so the gaps section shouldn't appear.
    assert "## Gaps To Close Before IC" not in out


def test_build_brief_surfaces_gaps_for_sparse_notes():
    raw = (FIXTURES / "sparse_notes.txt").read_text()
    notes = parse_notes(raw)
    out = build_brief(notes, llm_client=MockLLMClient())

    assert "## Gaps To Close Before IC" in out
    assert "**Ask**" in out
    assert "**Traction**" in out


def test_build_brief_defaults_to_mock_client_when_none_given():
    # Should not raise even though no llm_client argument is passed -
    # this is what makes the tool safe to run with no API key at all.
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    out = build_brief(notes)
    assert "# Investment Brief: Acme Robotics" in out


def test_executive_summary_reflects_problem_and_traction():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    out = build_brief(notes, llm_client=MockLLMClient())

    summary_section = out.split("## Executive Summary")[1].split("## Problem")[0]
    assert "20% of labor hours" in summary_section
    assert "$180k ARR" in summary_section
