from datetime import date
from pathlib import Path

from fakes import FakeChannel

from agent.adapters.radar_store import JsonRadarStore
from agent.radar.draft import RadarDraft
from agent.radar.feedback import read_verdicts
from agent.radar.pick import Pick, PostedPick, Verdict
from agent.radar.posting import post_radar

READER = "reader"
POSTED_ON = date(2026, 11, 2)
TODAY = date(2026, 11, 7)


def post_picks(tmp_path: Path, *titles: str) -> tuple[FakeChannel, JsonRadarStore]:
    """Posts one Radar with a Pick per title; returns the channel and the store."""
    channel = FakeChannel()
    store = JsonRadarStore(tmp_path / "radar.json")
    picks = [Pick(title=t, url=f"https://news.example.com/{t}", why_it_matters="w") for t in titles]
    post_radar(RadarDraft(picks=picks), POSTED_ON, channel, store)
    return channel, store


def message_of(picks: list[PostedPick], title: str) -> str:
    return next(pick.message_id for pick in picks if pick.title == title)


def test_the_readers_reactions_become_verdicts(tmp_path: Path) -> None:
    channel, store = post_picks(tmp_path, "liked", "disliked", "mixed", "untouched")
    picks = store.posted_picks()
    channel.react(READER, message_of(picks, "liked"), "👍")
    channel.react(READER, message_of(picks, "disliked"), "👎")
    channel.react(READER, message_of(picks, "mixed"), "👍")
    channel.react(READER, message_of(picks, "mixed"), "👎")

    readings = read_verdicts(picks, channel, READER, TODAY)

    assert {reading.pick.title: reading.verdict for reading in readings} == {
        "liked": Verdict.LIKED,
        "disliked": Verdict.DISLIKED,
        "mixed": Verdict.MIXED,
        "untouched": Verdict.NONE,
    }


def test_reactions_from_anyone_but_the_reader_are_ignored(tmp_path: Path) -> None:
    channel, store = post_picks(tmp_path, "liked by a friend")
    channel.react("friend", store.posted_picks()[0].message_id, "👍")

    [reading] = read_verdicts(store.posted_picks(), channel, READER, TODAY)

    assert reading.verdict is Verdict.NONE


def test_a_saved_verdict_reads_back_as_unchanged(tmp_path: Path) -> None:
    channel, store = post_picks(tmp_path, "liked")
    channel.react(READER, store.posted_picks()[0].message_id, "👍")
    [first] = read_verdicts(store.posted_picks(), channel, READER, TODAY)
    store.save_verdicts({first.pick.message_id: first.verdict})

    [again] = read_verdicts(store.posted_picks(), channel, READER, TODAY)

    assert first.changed
    assert again.verdict is Verdict.LIKED and not again.changed


def test_picks_older_than_the_window_are_left_alone(tmp_path: Path) -> None:
    channel, store = post_picks(tmp_path, "ancient")

    assert read_verdicts(store.posted_picks(), channel, READER, date(2026, 12, 31)) == []
