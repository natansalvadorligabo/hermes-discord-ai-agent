"""Picks: the Leads the agent chose for a Radar, how they read on Discord, and their Verdicts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from agent.radar.channel import DISLIKE, LIKE


class RadarError(Exception):
    pass


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
        """The Discord message for this Pick, e.g. `**1. Title**`, the why, the link, the topics."""
        lines = [f"**{number}. {self.title}**", self.why_it_matters, f"<{self.url}>"]
        if self.topics:
            lines.append("-# " + " · ".join(self.topics))
        return "\n".join(lines)


@dataclass(frozen=True)
class RadarDraft:
    picks: list[Pick]
    intro: str = ""

    @classmethod
    def from_json(cls, raw: object) -> RadarDraft:
        """The draft the agent wrote, e.g. `{"intro": "...", "picks": [{"title", "url", ...}]}`."""
        if not isinstance(raw, Mapping):
            raise RadarError(f"expected a JSON object with 'picks', got {type(raw).__name__}")
        picks = raw.get("picks")
        if not isinstance(picks, list) or not picks:
            raise RadarError("expected 'picks' to be a non-empty list")
        return cls(
            intro=str(raw.get("intro", "")),
            picks=[pick_from_json(item, f"picks[{i}]") for i, item in enumerate(picks)],
        )

    def header(self, day: date) -> str:
        lines = [f"## Applied AI Radar · {day:%a, %b} {day.day}"]
        if self.intro:
            lines.append(self.intro)
        lines.append(f"-# React {LIKE} or {DISLIKE} on each pick, or reply with what you want.")
        return "\n".join(lines)


@dataclass(frozen=True)
class PostedPick:
    title: str
    url: str
    message_id: str
    posted_on: date
    topics: tuple[str, ...] = ()
    verdict: Verdict = Verdict.NONE


@dataclass(frozen=True)
class VerdictChange:
    pick: PostedPick
    previous: Verdict
    verdict: Verdict


def pick_from_json(raw: object, where: str) -> Pick:
    if not isinstance(raw, Mapping):
        raise RadarError(f"expected {where} to be an object, got {type(raw).__name__}")
    topics = raw.get("topics", [])
    return Pick(
        title=required_text(raw, "title", where),
        url=required_text(raw, "url", where),
        why_it_matters=required_text(raw, "why_it_matters", where),
        topics=tuple(str(topic) for topic in topics) if isinstance(topics, list) else (),
    )


def required_text(raw: Mapping[str, object], key: str, where: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RadarError(f"expected {where}.{key} to be a non-empty string, got {value!r}")
    return value.strip()
