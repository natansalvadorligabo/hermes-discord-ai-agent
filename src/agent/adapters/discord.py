"""The Radar channel on Discord, over the REST API (see docs/adr/0001)."""

from __future__ import annotations

import time
from collections.abc import Callable
from urllib.parse import quote

from agent.adapters.http import HttpClient, HttpError, HttpRequest, HttpResponse
from agent.radar.channel import Reaction, SentMessage

API = "https://discord.com/api/v10"
SUPPRESS_EMBEDS = 1 << 2
MAX_RATE_LIMIT_RETRIES = 5


class RestDiscordChannel:
    """One text channel, reached with a bot token. Waits out 429 rate limits."""

    def __init__(
        self,
        channel_id: str,
        bot_token: str,
        http: HttpClient,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._channel_id = channel_id
        self._headers = {"Authorization": f"Bot {bot_token}"}
        self._http = http
        self._sleep = sleep

    def send_message(self, content: str) -> SentMessage:
        body = {"content": content, "flags": SUPPRESS_EMBEDS, "allowed_mentions": {"parse": []}}
        response = self._send("POST", f"/channels/{self._channel_id}/messages", body)
        message = response.json()
        if not isinstance(message, dict) or "id" not in message:
            raise HttpError(f"expected a message object with an id, got {response.text[:200]}")
        return SentMessage(message_id=str(message["id"]), channel_id=self._channel_id)

    def add_reaction(self, message_id: str, emoji: str) -> None:
        path = f"/channels/{self._channel_id}/messages/{message_id}/reactions/{quote(emoji)}/@me"
        self._send("PUT", path)

    def reactions_on(self, message_id: str) -> list[Reaction]:
        response = self._send("GET", f"/channels/{self._channel_id}/messages/{message_id}")
        message = response.json()
        raw = message.get("reactions", []) if isinstance(message, dict) else []
        return [reaction_from(item) for item in raw if isinstance(item, dict)]

    def _send(self, method: str, path: str, body: object = None) -> HttpResponse:
        request = HttpRequest(method=method, url=API + path, headers=self._headers, json_body=body)
        for _ in range(MAX_RATE_LIMIT_RETRIES):
            response = self._http.send(request)
            if response.status != 429:
                break
            self._sleep(float(response.headers.get("retry-after", "1")))
        if not response.is_success:
            raise HttpError(f"Discord {method} {path} answered {response.status}: {response.text}")
        return response


def reaction_from(raw: dict[str, object]) -> Reaction:
    emoji = raw.get("emoji")
    name = emoji.get("name") if isinstance(emoji, dict) else None
    count = raw.get("count")
    return Reaction(
        emoji=str(name or ""),
        count=count if isinstance(count, int) else 0,
        includes_bot=raw.get("me") is True,
    )
