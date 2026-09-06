"""Optional live web-news lookup for the company under evaluation.

Product decision worth spelling out: this is the one feature in the whole
tool that reaches out to the open internet, so — same pattern as
``llm_client.py`` — it's built behind a small protocol with a deterministic,
offline mock implementation (what the test suite runs against, and what
runs by default) and a real implementation that a partner opts into
explicitly with ``--news``. It should never fabricate headlines: if it
didn't run a real search, it says so, rather than pretending.

The real implementation intentionally needs no API key: it reads Google
News' public RSS search feed, which is free and unauthenticated.
"""

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class NewsItem:
    title: str
    source: str
    link: str
    published: str


@dataclass
class NewsResult:
    query: str
    items: list[NewsItem] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.items)


class NewsClient(Protocol):
    def search(self, company: str, limit: int = 5) -> NewsResult:
        ...


class MockNewsClient:
    """Deterministic, offline stand-in. Never touches the network.

    Returns zero items plus an explicit note that no live search ran,
    rather than fabricating headlines — the same "don't hide the gap"
    principle as ``MISSING_PLACEHOLDER`` in parser.py. This is what tests
    run against, and what the CLI uses unless ``--news`` is passed.
    """

    def search(self, company: str, limit: int = 5) -> NewsResult:
        return NewsResult(
            query=company,
            items=[],
            error=(
                f"No live search performed for '{company}' (offline mode). "
                "Run with --news to fetch real results."
            ),
        )


_GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


def _parse_rss(xml_text: str, limit: int) -> list[NewsItem]:
    """Parse a Google News RSS feed into ``NewsItem``s.

    Pulled out as its own function specifically so it can be unit-tested
    against a static XML fixture, without ever needing a live network call —
    the same reason ``_tool_agent_response`` in claude-agent-lab separates
    parsing from I/O.
    """
    root = ET.fromstring(xml_text)
    items: list[NewsItem] = []
    for item_el in root.findall("./channel/item")[:limit]:
        title = (item_el.findtext("title") or "").strip()
        link = (item_el.findtext("link") or "").strip()
        pub_date = (item_el.findtext("pubDate") or "").strip()
        source_el = item_el.find("source")
        tagged_source = (source_el.text or "").strip() if source_el is not None else ""

        # Google News titles are always formatted "Headline - Source",
        # whether or not an explicit <source> tag is also present. Split it
        # off either way, so "Source" never gets duplicated onto the end of
        # the headline in the rendered brief.
        if " - " in title:
            candidate_title, _, candidate_source = title.rpartition(" - ")
        else:
            candidate_title, candidate_source = title, ""

        if tagged_source:
            # Explicit tag wins; only strip the suffix off the title if it's
            # actually that same source (titles can legitimately contain
            # " - " elsewhere).
            source = tagged_source
            if candidate_source == tagged_source:
                title = candidate_title
        elif candidate_source:
            title, source = candidate_title, candidate_source
        else:
            source = ""
        items.append(NewsItem(title=title, source=source, link=link, published=pub_date))
    return items


class RealNewsClient:
    """Live lookup against Google News' public RSS search. No API key needed.

    Not exercised by the automated test suite (it requires real outbound
    internet access, which a CI box or a locked-down sandbox may not have);
    the RSS-parsing logic it shares with that path (``_parse_rss``) is
    tested directly against a static fixture instead. Runs fine on any
    ordinary computer with normal internet access.
    """

    def __init__(self, timeout: float = 6.0):
        self.timeout = timeout

    def search(self, company: str, limit: int = 5) -> NewsResult:
        query = urllib.parse.quote(f'"{company}"')
        url = _GOOGLE_NEWS_RSS.format(query=query)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "dealbrief/0.1"})
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                xml_text = response.read().decode("utf-8", errors="replace")
            items = _parse_rss(xml_text, limit)
            if not items:
                return NewsResult(
                    query=company,
                    items=[],
                    error=f"No recent news found for '{company}'.",
                )
            return NewsResult(query=company, items=items)
        except Exception as exc:  # network errors, DNS failures, malformed feed, ...
            return NewsResult(
                query=company,
                items=[],
                error=f"News search failed for '{company}': {exc}",
            )


def get_default_news_client(live: bool = False) -> NewsClient:
    """``live=True`` -> a real Google News lookup; otherwise the offline mock."""
    return RealNewsClient() if live else MockNewsClient()
