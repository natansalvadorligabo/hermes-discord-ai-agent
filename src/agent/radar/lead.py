"""Leads: recent links from the Sources that have never been posted in a Radar."""

from __future__ import annotations

from collections.abc import Container, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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
    leads: dict[str, Lead] = {}
    failures: list[SourceFailure] = []
    for source in sources:
        try:
            found = source.leads_since(since)
        # One dead feed must not cost the Reader the whole Radar, so any error is reported instead.
        except Exception as error:
            failures.append(SourceFailure(source=source.name, error=str(error)))
            continue
        for lead in found:
            key = canonical_url(lead.url)
            if key not in posted_urls and key not in leads:
                leads[key] = lead
    newest_first = sorted(leads.values(), key=lambda lead: lead.published_at, reverse=True)
    return LeadReport(leads=newest_first, failures=failures)
