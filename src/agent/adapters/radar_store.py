"""The Radar store kept as one JSON file in the agent's home folder."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from datetime import date
from pathlib import Path

from agent.radar.pick import PostedPick, Verdict


class JsonRadarStore:
    """Posted Picks in a JSON file, written whole on every change.

    Example: `JsonRadarStore(home / "radar.json").posted_urls()`
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def posted_picks(self) -> list[PostedPick]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return [posted_pick_from(item) for item in raw.get("picks", [])]

    def posted_urls(self) -> set[str]:
        return {pick.url for pick in self.posted_picks()}

    def record(self, picks: list[PostedPick]) -> None:
        self._write(self.posted_picks() + picks)

    def save_verdicts(self, verdicts: Mapping[str, Verdict]) -> None:
        if not verdicts:
            return
        self._write(
            [
                replace(pick, verdict=verdicts.get(pick.message_id, pick.verdict))
                for pick in self.posted_picks()
            ]
        )

    def _write(self, picks: list[PostedPick]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        body = {"picks": [posted_pick_as_json(pick) for pick in picks]}
        temporary = self._path.with_suffix(".tmp")
        temporary.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
        # Replace atomically so a crash mid-write never leaves a half-written store.
        temporary.replace(self._path)


def posted_pick_as_json(pick: PostedPick) -> dict[str, object]:
    return {
        "title": pick.title,
        "url": pick.url,
        "message_id": pick.message_id,
        "posted_on": pick.posted_on.isoformat(),
        "topics": list(pick.topics),
        "verdict": pick.verdict.value,
    }


def posted_pick_from(raw: dict[str, object]) -> PostedPick:
    topics = raw.get("topics")
    return PostedPick(
        title=str(raw["title"]),
        url=str(raw["url"]),
        message_id=str(raw["message_id"]),
        posted_on=date.fromisoformat(str(raw["posted_on"])),
        topics=tuple(str(topic) for topic in topics) if isinstance(topics, list) else (),
        verdict=Verdict(str(raw.get("verdict", Verdict.NONE.value))),
    )
