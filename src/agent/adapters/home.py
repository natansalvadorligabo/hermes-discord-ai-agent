"""The agent home: the folder outside the repo that holds one Reader's files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

HOME_VARIABLE = "DISCORD_AGENT_HOME"


@dataclass(frozen=True)
class AgentHome:
    root: Path

    @classmethod
    def from_environment(cls) -> AgentHome:
        """`$DISCORD_AGENT_HOME`, or `~/.discord-agent` when it is not set."""
        configured = os.environ.get(HOME_VARIABLE)
        return cls(Path(configured).expanduser() if configured else Path.home() / ".discord-agent")

    @property
    def reader_profile(self) -> Path:
        return self.root / "reader-profile.md"

    @property
    def sources(self) -> Path:
        return self.root / "sources.yaml"

    @property
    def radar_store(self) -> Path:
        return self.root / "radar.json"

    @property
    def drafts(self) -> Path:
        return self.root / "drafts"
