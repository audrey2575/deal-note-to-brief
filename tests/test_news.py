from pathlib import Path

from dealbrief.news import MockNewsClient, RealNewsClient, _parse_rss, get_default_news_client

FIXTURES = Path(__file__).parent / "fixtures"


def test_mock_news_client_never_fabricates_headlines():
    client = MockNewsClient()
    result = client.search("Acme Robotics")

    # The whole point of the mock: zero real network calls, zero invented
    # results. It should say plainly that no live search ran.
    assert result.items == []
    assert result.ok is False
    assert "Acme Robotics" in result.error
    assert "--news" in result.error


def test_get_default_news_client_returns_mock_unless_live_requested():
    assert isinstance(get_default_news_client(live=False), MockNewsClient)
    assert isinstance(get_default_news_client(live=True), RealNewsClient)


def test_parse_rss_extracts_title_link_source_and_date():
    xml_text = (FIXTURES / "google_news_sample.xml").read_text()
    items = _parse_rss(xml_text, limit=5)

    assert len(items) == 3
    first = items[0]
    assert first.title == "Acme Robotics closes new pilot with regional retailer"
    assert first.source == "TechCrunch"
    assert first.link == "https://news.google.com/rss/articles/example-1"
    assert "2026" in first.published


def test_parse_rss_falls_back_to_splitting_title_when_source_tag_is_absent():
    xml_text = (FIXTURES / "google_news_sample.xml").read_text()
    items = _parse_rss(xml_text, limit=5)

    # The second <item> in the fixture has no <source> tag and no " - " in
    # its title either, so it should come back with an empty source rather
    # than raising or guessing.
    second = items[1]
    assert second.title == "Why warehouse robotics is having a moment"
    assert second.source == ""

    third = items[2]
    assert third.title == "Acme Robotics named to regional startups-to-watch list"
    assert third.source == "Local Business Journal"


def test_parse_rss_respects_the_limit():
    xml_text = (FIXTURES / "google_news_sample.xml").read_text()
    items = _parse_rss(xml_text, limit=2)
    assert len(items) == 2
