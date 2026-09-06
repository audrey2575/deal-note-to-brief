from pathlib import Path

from dealbrief.brief import build_brief
from dealbrief.llm_client import MockLLMClient
from dealbrief.news import NewsItem, NewsResult
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


def test_header_shows_call_metadata_when_present():
    raw = (FIXTURES / "notes_with_meta.txt").read_text()
    notes = parse_notes(raw)
    out = build_brief(notes, llm_client=MockLLMClient())

    header = out.split("\n\n")[1]
    assert "**Date:** 2026-09-02" in header
    assert "Jamie Wu" in header
    assert "demo day" in header


def test_header_shows_placeholder_for_missing_call_metadata():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    out = build_brief(notes, llm_client=MockLLMClient())

    header = out.split("\n\n")[1]
    assert "**Date:** Not noted" in header
    assert "**Attendees:** Not noted" in header
    assert "**How We Met:** Not noted" in header


def test_news_section_is_omitted_when_no_news_result_passed():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    out = build_brief(notes, llm_client=MockLLMClient())
    assert "## Recent News" not in out


def test_news_section_lists_items_when_a_news_result_is_passed():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    news = NewsResult(
        query="Acme Robotics",
        items=[
            NewsItem(
                title="Acme Robotics closes new pilot with regional retailer",
                source="TechCrunch",
                link="https://example.com/acme-pilot",
                published="Mon, 01 Sep 2026 12:00:00 GMT",
            )
        ],
    )
    out = build_brief(notes, llm_client=MockLLMClient(), news=news)

    assert "## Recent News" in out
    assert "Acme Robotics closes new pilot" in out
    assert "TechCrunch" in out
    assert "https://example.com/acme-pilot" in out


def test_news_section_surfaces_the_error_when_search_found_nothing():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    news = NewsResult(query="Acme Robotics", items=[], error="No recent news found for 'Acme Robotics'.")
    out = build_brief(notes, llm_client=MockLLMClient(), news=news)

    assert "## Recent News" in out
    assert "No recent news found" in out
