"""Test doubles for the HTTP boundary and the Radar channel."""

from __future__ import annotations

from dataclasses import dataclass, field

from agent.adapters.http import HttpRequest, HttpResponse

BOT_ID = "bot"


class FakeHttpClient:
    """Answers from canned responses keyed by URL; a list answers in order, one per request.

    Unknown URLs fail like a dead host.
    """

    def __init__(self, responses: dict[str, HttpResponse | list[HttpResponse]]) -> None:
        self._responses = responses
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        if request.url not in self._responses:
            raise ConnectionError(f"no route to {request.url}")
        answer = self._responses[request.url]
        return answer.pop(0) if isinstance(answer, list) else answer


def ok(text: str) -> HttpResponse:
    return HttpResponse(status=200, text=text, headers={})


@dataclass
class FakeChannel:
    """An in-memory Radar channel. Message IDs are "m1", "m2"... in sending order."""

    messages: dict[str, str] = field(default_factory=dict)
    reactions: dict[tuple[str, str], set[str]] = field(default_factory=dict)

    def send_message(self, content: str) -> str:
        message_id = f"m{len(self.messages) + 1}"
        self.messages[message_id] = content
        return message_id

    def add_reaction(self, message_id: str, emoji: str) -> None:
        self.react(BOT_ID, message_id, emoji)

    def people_who_reacted(self, message_id: str, emoji: str) -> set[str]:
        return set(self.reactions.get((message_id, emoji), set()))

    def react(self, person: str, message_id: str, emoji: str) -> None:
        self.reactions.setdefault((message_id, emoji), set()).add(person)
