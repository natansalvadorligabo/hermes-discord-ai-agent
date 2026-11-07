"""Leads: recent links from the Sources that have never been posted in a Radar."""

from __future__ import annotations

from collections.abc import Container, Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

MIN_WINDOW = timedelta(hours=36)
MAX_WINDOW = timedelta(days=7)
TRACKING_PARAMS = frozenset({"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source"})


@dataclass(frozen=True)
class Lead:
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str = ""
    points: int | None = None


@dataclass(frozen=True)
class SourceFailure:
    source: str
    error: str


@dataclass(frozen=True)
class LeadReport:
    leads: list[Lead]
    failures: list[SourceFailure]


class Source(Protocol):
    name: str

    def leads_since(self, since: datetime) -> list[Lead]: ...


def canonical_url(url: str) -> str:
    """The form of a URL used to tell whether two links are the same story.

    Example: `canonical_url("HTTPS://Blog.dev/post/?utm_source=x#top")` -> `"https://blog.dev/post"`
    """
    parts = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.startswith("utm_") and key not in TRACKING_PARAMS
    ]
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def collect_leads(
    sources: Iterable[Source], since: datetime, posted_urls: Container[str]
) -> LeadReport:
    """Every Lead published since `since`, newest first, one per link, posted links left out.

    A Source that fails is reported in `failures` and the others still count.
    Example: `collect_leads(sources, since=yesterday, posted_urls=store.posted_urls())`
    """
    found: list[Lead] = []
    failures: list[SourceFailure] = []
    for source in sources:
        try:
            found += source.leads_since(since)
        # One dead feed must not cost the Reader the whole Radar, so any error is reported instead.
        except Exception as error:
            failures.append(SourceFailure(source=source.name, error=str(error)))
    leads = _one_per_story(found, posted_urls)
    newest_first = sorted(leads, key=lambda lead: lead.published_at, reverse=True)
    return LeadReport(leads=newest_first, failures=failures)


def leads_window_start(now: datetime, last_radar_day: date | None) -> datetime:
    """Where the search for Leads starts: back to the last Radar's day, within 36 hours to 7 days.

    Reaching back to the last Radar covers weekends and any schedule the Reader picked;
    posted links are left out anyway, so a wider window never repeats a Pick.
    Example: `leads_window_start(datetime.now(UTC), store.last_radar_day())`
    """
    start = now - MIN_WINDOW
    if last_radar_day is not None:
        start = min(start, datetime.combine(last_radar_day, time(), tzinfo=UTC))
    return max(start, now - MAX_WINDOW)


def _one_per_story(leads: list[Lead], posted_urls: Container[str]) -> list[Lead]:
    """The first Lead for each canonical URL, in Source order, never one already posted."""
    by_url: dict[str, Lead] = {}
    for lead in leads:
        by_url.setdefault(canonical_url(lead.url), lead)
    return [lead for url, lead in by_url.items() if url not in posted_urls]
