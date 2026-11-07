from datetime import date
from pathlib import Path

import pytest
from fakes import FakeDiscordChannel

from agent.adapters.radar_store import JsonRadarStore
from agent.radar.pick import Pick, RadarDraft, RadarError
from agent.radar.posting import post_radar

DAY = date(2026, 11, 7)


def draft(*picks: Pick) -> RadarDraft:
    return RadarDraft(intro="Two things worth your morning.", picks=list(picks))


SANDBOXES = Pick(
    title="Sandboxing coding agents",
    url="https://blog.example.com/sandboxes/?utm_source=rss",
    why_it_matters="A concrete recipe for running agents with no network by default.",
    topics=("sandboxes", "agents"),
)
EVALS = Pick(
    title="Evals in CI",
    url="https://blog.example.com/evals",
    why_it_matters="Shows how to fail a PR when a prompt change drops eval scores.",
    topics=("evals",),
)


def test_posts_a_header_then_one_message_per_pick_with_like_and_dislike_buttons(
    tmp_path: Path,
) -> None:
    channel = FakeDiscordChannel()

    post_radar(draft(SANDBOXES, EVALS), DAY, channel, JsonRadarStore(tmp_path / "radar.json"))

    header, first, second = channel.messages.values()
    assert "Radar" in header and "Sat, Nov 7" in header
    assert "Two things worth your morning." in header
    assert first.startswith("**1. Sandboxing coding agents**")
    assert "<https://blog.example.com/sandboxes/?utm_source=rss>" in first
    assert "sandboxes · agents" in first
    assert second.startswith("**2. Evals in CI**")
    assert channel.own_reactions == {"1001": ["👍", "👎"], "1002": ["👍", "👎"]}


def test_posted_links_are_remembered_across_runs(tmp_path: Path) -> None:
    path = tmp_path / "radar.json"

    post_radar(draft(SANDBOXES), DAY, FakeDiscordChannel(), JsonRadarStore(path))

    assert JsonRadarStore(path).posted_urls() == {"https://blog.example.com/sandboxes"}


def test_nothing_is_posted_when_a_pick_does_not_fit_in_one_message(tmp_path: Path) -> None:
    channel = FakeDiscordChannel()
    rambling = Pick(title="Too long", url="https://x.dev", why_it_matters="a" * 2100, topics=())

    with pytest.raises(RadarError, match="Pick 2 .* 2000"):
        post_radar(
            draft(SANDBOXES, rambling), DAY, channel, JsonRadarStore(tmp_path / "radar.json")
        )

    assert channel.messages == {}


def test_a_draft_is_read_from_the_json_the_agent_writes() -> None:
    raw = {
        "intro": "Hi",
        "picks": [
            {
                "title": "Evals in CI",
                "url": "https://blog.example.com/evals",
                "why_it_matters": "Gate PRs on evals.",
                "topics": ["evals"],
            }
        ],
    }

    assert RadarDraft.from_json(raw) == RadarDraft(
        intro="Hi",
        picks=[
            Pick(
                title="Evals in CI",
                url="https://blog.example.com/evals",
                why_it_matters="Gate PRs on evals.",
                topics=("evals",),
            )
        ],
    )


def test_a_draft_without_a_pick_url_names_the_missing_field() -> None:
    with pytest.raises(RadarError, match=r"picks\[0\].url"):
        RadarDraft.from_json({"picks": [{"title": "x", "why_it_matters": "y"}]})
