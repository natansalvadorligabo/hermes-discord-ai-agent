from datetime import date
from pathlib import Path

from fakes import FakeDiscordChannel

from agent.adapters.radar_store import JsonRadarStore
from agent.radar.channel import Reaction
from agent.radar.feedback import sync_verdicts
from agent.radar.pick import Pick, RadarDraft, Verdict
from agent.radar.posting import post_radar

POSTED_ON = date(2026, 11, 2)


def pick(title: str) -> Pick:
    return Pick(title=title, url=f"https://news.example.com/{title}", why_it_matters="w", topics=())


def posted(tmp_path: Path, *titles: str) -> tuple[FakeDiscordChannel, JsonRadarStore]:
    channel = FakeDiscordChannel()
    store = JsonRadarStore(tmp_path / "radar.json")
    picks = [pick(title) for title in titles]
    post_radar(RadarDraft(picks=picks), POSTED_ON, channel, store)
    return channel, store


def bot_buttons(likes: int = 1, dislikes: int = 1) -> list[Reaction]:
    return [
        Reaction(emoji="👍", count=likes, includes_bot=True),
        Reaction(emoji="👎", count=dislikes, includes_bot=True),
    ]


def test_reader_reactions_become_verdicts(tmp_path: Path) -> None:
    channel, store = posted(tmp_path, "liked", "disliked", "mixed", "untouched")
    channel.reactions = {
        "1001": bot_buttons(likes=2),
        "1002": bot_buttons(dislikes=2),
        "1003": bot_buttons(likes=2, dislikes=2),
        "1004": bot_buttons(),
    }

    changes = sync_verdicts(store, channel, today=date(2026, 11, 7))

    assert [(change.pick.title, change.verdict) for change in changes] == [
        ("liked", Verdict.LIKED),
        ("disliked", Verdict.DISLIKED),
        ("mixed", Verdict.MIXED),
    ]
    saved = {p.title: p.verdict for p in JsonRadarStore(tmp_path / "radar.json").posted_picks()}
    assert saved["liked"] is Verdict.LIKED and saved["untouched"] is Verdict.NONE


def test_only_verdicts_that_changed_since_the_last_sync_are_reported(tmp_path: Path) -> None:
    channel, store = posted(tmp_path, "liked")
    channel.reactions = {"1001": bot_buttons(likes=2)}
    sync_verdicts(store, channel, today=date(2026, 11, 7))

    assert sync_verdicts(store, channel, today=date(2026, 11, 8)) == []

    channel.reactions = {"1001": bot_buttons(dislikes=2)}
    changes = sync_verdicts(store, channel, today=date(2026, 11, 9))
    assert [(change.previous, change.verdict) for change in changes] == [
        (Verdict.LIKED, Verdict.DISLIKED)
    ]


def test_picks_older_than_the_window_are_left_alone(tmp_path: Path) -> None:
    channel, store = posted(tmp_path, "ancient")
    channel.reactions = {"1001": bot_buttons(likes=2)}

    assert sync_verdicts(store, channel, today=date(2026, 12, 31), window_days=14) == []
