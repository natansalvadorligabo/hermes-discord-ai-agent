"""The Radar channel port: where the Radar is posted and where the Reader reacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

MESSAGE_LIMIT = 2000
LIKE = "👍"
DISLIKE = "👎"


@dataclass(frozen=True)
class SentMessage:
    message_id: str
    channel_id: str


@dataclass(frozen=True)
class Reaction:
    emoji: str
    count: int
    includes_bot: bool

    @property
    def people(self) -> int:
        """How many people reacted, not counting the bot's own reaction."""
        return self.count - (1 if self.includes_bot else 0)


class Channel(Protocol):
    def send_message(self, content: str) -> SentMessage: ...

    def add_reaction(self, message_id: str, emoji: str) -> None: ...

    def reactions_on(self, message_id: str) -> list[Reaction]: ...
