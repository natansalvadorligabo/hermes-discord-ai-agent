"""The Radar channel port: where the Radar is posted and where the Reader reacts."""

from __future__ import annotations

from typing import Protocol

MESSAGE_LIMIT = 2000
LIKE = "👍"
DISLIKE = "👎"


class Channel(Protocol):
    def send_message(self, content: str) -> str:
        """Post `content` and return the new message's ID."""
        ...

    def add_reaction(self, message_id: str, emoji: str) -> None: ...

    def people_who_reacted(self, message_id: str, emoji: str) -> set[str]:
        """IDs of everyone who reacted with `emoji`, the bot included."""
        ...
