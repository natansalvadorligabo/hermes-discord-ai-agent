"""The Radar channel on Discord, over the REST API (see docs/adr/0001)."""

from __future__ import annotations

import time
from collections.abc import Callable
from urllib.parse import quote

from agent.adapters.http import HttpClient, HttpError, HttpRequest, HttpResponse

API = "https://discord.com/api/v10"
SUPPRESS_EMBEDS = 1 << 2
MAX_RATE_LIMIT_RETRIES = 5
MAX_REACTORS = 100


class RestDiscordChannel:
    """One text channel, reached with a bot token. Waits out 429 rate limits.

    Example: `RestDiscordChannel(channel_id="123", bot_token=token, http=HttpxClient())`
    """

    def __init__(
        self,
        channel_id: str,
        bot_token: str,
        http: HttpClient,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._messages = f"/channels/{channel_id}/messages"
        self._headers = {"Authorization": f"Bot {bot_token}"}
        self._http = http
        self._sleep = sleep

    def send_message(self, content: str) -> str:
        """Post `content` with link previews off and no pings; return the message ID."""
        body = {"content": content, "flags": SUPPRESS_EMBEDS, "allowed_mentions": {"parse": []}}
        message = self._send(HttpRequest("POST", API + self._messages, json_body=body)).json()
        if not isinstance(message, dict) or "id" not in message:
            raise HttpError(f"expected a Discord message object with an id, got {message!r:.200}")
        return str(message["id"])

    def add_reaction(self, message_id: str, emoji: str) -> None:
        """React to a message as the bot, e.g. `channel.add_reaction("123", "👍")`."""
        self._send(HttpRequest("PUT", self._reactions_url(message_id, emoji) + "/@me"))

    def people_who_reacted(self, message_id: str, emoji: str) -> set[str]:
        """User IDs that reacted with `emoji` (first 100), e.g. `{"4815", "1623"}`."""
        url = self._reactions_url(message_id, emoji)
        users = self._send(HttpRequest("GET", url, params={"limit": str(MAX_REACTORS)})).json()
        if not isinstance(users, list):
            raise HttpError(f"expected a list of Discord users, got {users!r:.200}")
        return {str(user["id"]) for user in users if isinstance(user, dict) and "id" in user}

    def _reactions_url(self, message_id: str, emoji: str) -> str:
        return f"{API}{self._messages}/{message_id}/reactions/{quote(emoji)}"

    def _send(self, request: HttpRequest) -> HttpResponse:
        request = HttpRequest(
            request.method, request.url, request.params, self._headers, request.json_body
        )
        for _ in range(MAX_RATE_LIMIT_RETRIES):
            response = self._http.send(request)
            if response.status != 429:
                break
            self._sleep(float(response.headers.get("retry-after", "1")))
        if not response.is_success:
            raise HttpError(
                f"Discord {request.method} {request.url} answered {response.status}, "
                f"expected 2xx: {response.text:.200}"
            )
        return response
