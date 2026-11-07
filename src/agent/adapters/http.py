"""The HTTP boundary. httpx appears only in this file."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

import httpx

USER_AGENT = (
    "hermes-discord-ai-agent (+https://github.com/natansalvadorligabo/hermes-discord-ai-agent)"
)


@dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    params: Mapping[str, str] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    json_body: object = None


@dataclass(frozen=True)
class HttpResponse:
    status: int
    text: str
    headers: Mapping[str, str]

    def json(self) -> object:
        """The body parsed as JSON, e.g. `response.json()` -> `{"hits": [...]}`."""
        parsed: object = json.loads(self.text)
        return parsed

    @property
    def is_success(self) -> bool:
        return 200 <= self.status < 300


class HttpClient(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse: ...


class HttpxClient:
    """Sends requests with httpx, following redirects, with a short timeout."""

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )

    def send(self, request: HttpRequest) -> HttpResponse:
        response = self._client.request(
            request.method,
            request.url,
            params=dict(request.params),
            headers=dict(request.headers),
            json=request.json_body,
        )
        return HttpResponse(
            status=response.status_code, text=response.text, headers=dict(response.headers)
        )


def get_text(http: HttpClient, url: str, params: Mapping[str, str] | None = None) -> str:
    """GET a URL and return its body, raising on a non-2xx status.

    Example: `get_text(http, "https://simonwillison.net/atom/everything/")`
    """
    response = http.send(HttpRequest(method="GET", url=url, params=params or {}))
    if not response.is_success:
        raise HttpError(f"GET {url} answered {response.status}, expected 2xx")
    return response.text


class HttpError(Exception):
    pass
