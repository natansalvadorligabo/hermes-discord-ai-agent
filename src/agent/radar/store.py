"""The Radar store port: every Pick ever posted and its latest Verdict."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Protocol

from agent.radar.pick import PostedPick, Verdict


class RadarStore(Protocol):
    def posted_picks(self) -> list[PostedPick]: ...

    def posted_urls(self) -> set[str]: ...

    def last_radar_day(self) -> date | None: ...

    def record(self, picks: list[PostedPick]) -> None: ...

    def save_verdicts(self, verdicts: Mapping[str, Verdict]) -> None:
        """Store each Verdict against the Pick posted as that message ID."""
        ...
