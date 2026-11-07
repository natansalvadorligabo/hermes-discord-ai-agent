"""Test doubles for the HTTP boundary and the Discord channel."""

from __future__ import annotations

from dataclasses import dataclass, field

from agent.adapters.http import HttpRequest, HttpResponse
from agent.radar.channel import Reaction, SentMessage


class FakeHttpClient:
    """Answers requests from canned responses keyed by URL; unknown URLs fail like a dead host."""

    def __init__(self, responses: dict[str, HttpResponse]) -> None:
        self._responses = responses
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        if request.url not in self._responses:
            raise ConnectionError(f"no route to {request.url}")
        return self._responses[request.url]


def ok(text: str) -> HttpResponse:
    return HttpResponse(status=200, text=text, headers={})


@dataclass
class FakeDiscordChannel:
    """An in-memory channel: keeps sent messages and lets tests set reactions on them."""

    messages: dict[str, str] = field(default_factory=dict)
    own_reactions: dict[str, list[str]] = field(default_factory=dict)
    reactions: dict[str, list[Reaction]] = field(default_factory=dict)

    def send_message(self, content: str) -> SentMessage:
        message_id = str(1000 + len(self.messages))
        self.messages[message_id] = content
        return SentMessage(message_id=message_id, channel_id="trends")

    def add_reaction(self, message_id: str, emoji: str) -> None:
        self.own_reactions.setdefault(message_id, []).append(emoji)

    def reactions_on(self, message_id: str) -> list[Reaction]:
        return self.reactions.get(message_id, [])
