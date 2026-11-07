"""The Radar draft: what the agent writes before posting, read from JSON and checked."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from agent.radar.channel import DISLIKE, LIKE
from agent.radar.pick import Pick, topics_from

DEFAULT_FOOTER = f"React {LIKE} or {DISLIKE} on each pick, or reply with what you want."


class DraftError(Exception):
    pass


@dataclass(frozen=True)
class RadarDraft:
    """The Radar before it is posted. `title` and `footer` let the agent write in any language."""

    picks: list[Pick]
    intro: str = ""
    title: str = ""
    footer: str = DEFAULT_FOOTER

    @classmethod
    def from_json(cls, raw: object) -> RadarDraft:
        """The draft the agent wrote, e.g. `{"intro": "...", "picks": [{"title", "url", ...}]}`."""
        if not isinstance(raw, Mapping):
            raise DraftError(f"expected a JSON object with 'picks', got {type(raw).__name__}")
        picks = raw.get("picks")
        if not isinstance(picks, list) or not picks:
            raise DraftError(f"expected 'picks' to be a non-empty list, got {picks!r}")
        return cls(
            picks=[_pick_from(item, f"picks[{i}]") for i, item in enumerate(picks)],
            intro=str(raw.get("intro", "")),
            title=str(raw.get("title", "")),
            footer=str(raw.get("footer", DEFAULT_FOOTER)),
        )

    def header(self, day: date) -> str:
        """The first message of the Radar, e.g. `"## Applied AI Radar · Sat, Nov 7\\n..."`."""
        title = self.title or f"Applied AI Radar · {day:%a, %b} {day.day}"
        lines = [f"## {title}", self.intro, f"-# {self.footer}" if self.footer else ""]
        return "\n".join(line for line in lines if line)


def _pick_from(raw: object, where: str) -> Pick:
    if not isinstance(raw, Mapping):
        raise DraftError(f"expected {where} to be an object, got {type(raw).__name__}")
    return Pick(
        title=_required_text(raw, "title", where),
        url=_required_text(raw, "url", where),
        why_it_matters=_required_text(raw, "why_it_matters", where),
        topics=topics_from(raw.get("topics")),
    )


def _required_text(raw: Mapping[str, object], key: str, where: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DraftError(f"expected {where}.{key} to be a non-empty string, got {value!r}")
    return value.strip()
