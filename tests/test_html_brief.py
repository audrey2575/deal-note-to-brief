from pathlib import Path

from dealbrief.html_brief import render_html_brief
from dealbrief.llm_client import MockLLMClient
from dealbrief.news import NewsItem, NewsResult
from dealbrief.parser import parse_notes

FIXTURES = Path(__file__).parent / "fixtures"


def test_render_html_brief_produces_a_self_contained_page():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    out = render_html_brief(notes, llm_client=MockLLMClient())

    assert out.startswith("<!doctype html>")
    assert "<title>Investment Brief — Acme Robotics</title>" in out
    assert "<style>" in out
    # No external assets: everything (CSS, structure) must be inline so the
    # file opens correctly by double-clicking it, with no network involved.
    assert "http://" not in out.split("<style>")[0]
    assert "<script src=" not in out


def test_render_html_brief_includes_call_metadata_and_core_sections():
    raw = (FIXTURES / "notes_with_meta.txt").read_text()
    notes = parse_notes(raw)
    out = render_html_brief(notes, llm_client=MockLLMClient())

    assert "Northwind Analytics" in out
    assert "2026-09-02" in out
    assert "Jamie Wu" in out
    assert "demo day" in out
    for heading in ["Problem", "Solution", "Traction", "Team", "Risks &amp; Open Questions"]:
        assert heading in out


def test_render_html_brief_escapes_note_content():
    raw = "Company: <script>alert(1)</script> Corp\nSector: Test\nStage: Seed\nAsk: $1M\n"
    notes = parse_notes(raw)
    out = render_html_brief(notes, llm_client=MockLLMClient())

    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out


def test_render_html_brief_shows_gaps_section_for_sparse_notes():
    raw = (FIXTURES / "sparse_notes.txt").read_text()
    notes = parse_notes(raw)
    out = render_html_brief(notes, llm_client=MockLLMClient())

    assert "Gaps To Close Before IC" in out
    assert "Ask" in out


def test_render_html_brief_includes_news_section_when_passed():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    news = NewsResult(
        query="Acme Robotics",
        items=[
            NewsItem(
                title="Acme Robotics closes new pilot",
                source="TechCrunch",
                link="https://example.com/acme",
                published="Mon, 01 Sep 2026 12:00:00 GMT",
            )
        ],
    )
    out = render_html_brief(notes, llm_client=MockLLMClient(), news=news)

    assert "Recent News" in out
    assert "Acme Robotics closes new pilot" in out
    assert 'href="https://example.com/acme"' in out
    assert "TechCrunch" in out


def test_render_html_brief_omits_news_section_when_not_passed():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    out = render_html_brief(notes, llm_client=MockLLMClient())
    assert "Recent News" not in out
