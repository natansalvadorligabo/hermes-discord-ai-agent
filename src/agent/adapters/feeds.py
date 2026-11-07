"""Sources: feeds and Hacker News searches. feedparser appears only in this file."""

from __future__ import annotations

import calendar
import html
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser

from agent.adapters.http import HttpClient, HttpError, get_text
from agent.radar.lead import Lead

HACKER_NEWS_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
SUMMARY_LIMIT = 400
TAG = re.compile(r"<[^>]+>")
WHITESPACE = re.compile(r"\s+")


@dataclass
class FeedSource:
    """An RSS or Atom feed: a blog, a newsletter, or GitHub releases (`.../releases.atom`).

    Example: `FeedSource("Simon Willison", "https://simonwillison.net/atom/everything/", http)`
    """

    name: str
    url: str
    http: HttpClient
    max_leads: int = 15

    def leads_since(self, since: datetime) -> list[Lead]:
        """Dated entries published since `since`, at most `max_leads`; undated ones are skipped."""
        feed = feedparser.parse(get_text(self.http, self.url))
        leads = [lead for entry in feed.entries if (lead := self._lead_from(entry)) is not None]
        return [lead for lead in leads if lead.published_at >= since][: self.max_leads]

    def _lead_from(self, entry: feedparser.FeedParserDict) -> Lead | None:
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        link = entry.get("link")
        # Undated entries cannot be placed in the time window, so they never become Leads.
        if published is None or not link:
            return None
        return Lead(
            title=plain_text(str(entry.get("title", link))),
            url=str(link),
            source=self.name,
            published_at=datetime.fromtimestamp(calendar.timegm(published), tz=UTC),
            summary=plain_text(str(entry.get("summary", ""))),
        )


@dataclass
class HackerNewsSource:
    """Hacker News stories matching a query, through the Algolia search API.

    Example: `HackerNewsSource("HN: agents", query="AI agent", http=http, min_points=50)`
    """

    name: str
    query: str
    http: HttpClient
    min_points: int = 30
    max_leads: int = 15

    def leads_since(self, since: datetime) -> list[Lead]:
        """Stories posted since `since` with at least `min_points`, at most `max_leads`."""
        params = {
            "query": self.query,
            "tags": "story",
            "numericFilters": f"created_at_i>={int(since.timestamp())},points>={self.min_points}",
            "hitsPerPage": str(self.max_leads),
        }
        body = json.loads(get_text(self.http, HACKER_NEWS_SEARCH_URL, params))
        hits = body.get("hits") if isinstance(body, dict) else None
        if not isinstance(hits, list):
            raise HttpError(
                f"expected a JSON object with a 'hits' list from {self.name}, got {body!r:.200}"
            )
        leads = [self._lead_from(hit) for hit in hits if isinstance(hit, dict)]
        return [lead for lead in leads if lead.published_at >= since]

    def _lead_from(self, hit: dict[str, object]) -> Lead:
        story_id = str(hit.get("objectID", ""))
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={story_id}"
        points = hit.get("points")
        created = hit.get("created_at_i")
        return Lead(
            title=str(hit.get("title", "")),
            url=str(url),
            source=self.name,
            published_at=datetime.fromtimestamp(int(str(created or 0)), tz=UTC),
            points=points if isinstance(points, int) else None,
        )


def plain_text(markup: str) -> str:
    """Markup reduced to one line of text, cut to SUMMARY_LIMIT characters.

    Example: `plain_text("<p>Hello &amp; <b>bye</b></p>")` -> `"Hello & bye"`
    """
    text = WHITESPACE.sub(" ", html.unescape(TAG.sub(" ", markup))).strip()
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    if len(text) <= SUMMARY_LIMIT:
        return text
    return text[: SUMMARY_LIMIT - 1].rstrip() + "…"
