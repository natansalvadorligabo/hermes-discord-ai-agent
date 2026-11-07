"""Picks: the Leads the agent chose for a Radar, and the Reader's Verdict once posted."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from agent.radar.lead import canonical_url


class Verdict(StrEnum):
    NONE = "none"
    LIKED = "liked"
    DISLIKED = "disliked"
    MIXED = "mixed"


@dataclass(frozen=True)
class Pick:
    title: str
    url: str
    why_it_matters: str
    topics: tuple[str, ...] = ()

    def as_message(self, number: int) -> str:
        """The Pick as one Discord message.

        Example: `pick.as_message(1)` -> `"**1. Title**\\nWhy...\\n<https://...>\\n-# evals · ci"`
        """
        lines = [f"**{number}. {self.title}**", self.why_it_matters, f"<{self.url}>"]
        if self.topics:
            lines.append("-# " + " · ".join(self.topics))
        return "\n".join(lines)

    def posted_as(self, message_id: str, day: date) -> PostedPick:
        """This Pick as recorded once posted, e.g. `pick.posted_as("123", date.today())`."""
        return PostedPick(
            title=self.title,
            url=canonical_url(self.url),
            message_id=message_id,
            posted_on=day,
            topics=self.topics,
        )


@dataclass(frozen=True)
class PostedPick:
    """A Pick as posted. Its `url` is canonical, so it matches Leads for the same story."""

    title: str
    url: str
    message_id: str
    posted_on: date
    topics: tuple[str, ...] = ()
    verdict: Verdict = Verdict.NONE


def topics_from(raw: object) -> tuple[str, ...]:
    """Topic tags from a JSON value, e.g. `topics_from(["evals", "ci"])` -> `("evals", "ci")`."""
    return tuple(str(topic) for topic in raw) if isinstance(raw, list) else ()
