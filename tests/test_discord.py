from fakes import FakeHttpClient, ok

from agent.adapters.discord import API, RestDiscordChannel
from agent.adapters.http import HttpResponse

REACTORS = f"{API}/channels/c1/messages/m1/reactions/%F0%9F%91%8D"


def test_waits_out_a_rate_limit_and_retries() -> None:
    waits: list[float] = []
    http = FakeHttpClient(
        {
            REACTORS: [
                HttpResponse(status=429, text="{}", headers={"retry-after": "0.5"}),
                ok('[{"id": "reader"}, {"id": "bot"}]'),
            ]
        }
    )
    channel = RestDiscordChannel(channel_id="c1", bot_token="t", http=http, sleep=waits.append)

    assert channel.people_who_reacted("m1", "👍") == {"reader", "bot"}
    assert waits == [0.5]
    assert http.requests[0].headers["Authorization"] == "Bot t"
