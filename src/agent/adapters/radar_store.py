"""The Radar store kept as one JSON file in the agent home."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from datetime import date
from pathlib import Path

from agent.radar.pick import PostedPick, Verdict, topics_from


class StoreError(Exception):
    pass


class JsonRadarStore:
    """Posted Picks in a JSON file, written whole on every change.

    Example: `JsonRadarStore(home.radar_store).posted_urls()`
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def posted_picks(self) -> list[PostedPick]:
        """Every Pick ever posted, oldest first; empty before the first Radar."""
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return [self._posted_pick_from(item) for item in raw.get("picks", [])]

    def posted_urls(self) -> set[str]:
        """Canonical URLs of every posted Pick, e.g. `{"https://blog.dev/post"}`."""
        return {pick.url for pick in self.posted_picks()}

    def last_radar_day(self) -> date | None:
        """The day of the most recent Radar, or None before the first one."""
        return max((pick.posted_on for pick in self.posted_picks()), default=None)

    def record(self, picks: list[PostedPick]) -> None:
        """Add newly posted Picks, e.g. `store.record([pick.posted_as("123", today)])`."""
        self._write(self.posted_picks() + picks)

    def save_verdicts(self, verdicts: Mapping[str, Verdict]) -> None:
        """Store Verdicts by message ID, e.g. `store.save_verdicts({"123": Verdict.LIKED})`."""
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
        body = {"picks": [_as_json(pick) for pick in picks]}
        temporary = self._path.with_suffix(".tmp")
        temporary.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
        # Replace atomically so a crash mid-write never leaves a half-written store.
        temporary.replace(self._path)

    def _posted_pick_from(self, raw: dict[str, object]) -> PostedPick:
        try:
            return PostedPick(
                title=str(raw["title"]),
                url=str(raw["url"]),
                message_id=str(raw["message_id"]),
                posted_on=date.fromisoformat(str(raw["posted_on"])),
                topics=topics_from(raw.get("topics")),
                verdict=Verdict(str(raw.get("verdict", Verdict.NONE.value))),
            )
        except (KeyError, ValueError) as error:
            raise StoreError(
                f"expected a posted Pick with title, url, message_id and an ISO posted_on "
                f"in {self._path}, got {raw!r:.200} ({error})"
            ) from error


def _as_json(pick: PostedPick) -> dict[str, object]:
    return {
        "title": pick.title,
        "url": pick.url,
        "message_id": pick.message_id,
        "posted_on": pick.posted_on.isoformat(),
        "topics": list(pick.topics),
        "verdict": pick.verdict.value,
    }
