"""Feedback from reactions: the Reader's 👍/👎 on posted Picks, read as Verdicts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from agent.radar.channel import DISLIKE, LIKE, Channel
from agent.radar.pick import PostedPick, Verdict

VERDICT_WINDOW_DAYS = 14
VERDICTS = {
    (True, False): Verdict.LIKED,
    (False, True): Verdict.DISLIKED,
    (True, True): Verdict.MIXED,
    (False, False): Verdict.NONE,
}


@dataclass(frozen=True)
class VerdictReading:
    """The Verdict read now on a posted Pick; `changed` when it differs from the saved one."""

    pick: PostedPick
    verdict: Verdict

    @property
    def changed(self) -> bool:
        return self.verdict is not self.pick.verdict


def read_verdicts(
    picks: list[PostedPick],
    channel: Channel,
    reader_id: str,
    today: date,
    window_days: int = VERDICT_WINDOW_DAYS,
) -> list[VerdictReading]:
    """The Reader's Verdict on every Pick posted in the last `window_days`.

    Only the Reader's own reactions count. Saving them is the caller's choice.
    Example: `read_verdicts(store.posted_picks(), channel, reader_id="123", today=date.today())`
    """
    oldest = today - timedelta(days=window_days)
    return [
        VerdictReading(pick=pick, verdict=_reader_verdict(pick.message_id, channel, reader_id))
        for pick in picks
        if pick.posted_on >= oldest
    ]


def _reader_verdict(message_id: str, channel: Channel, reader_id: str) -> Verdict:
    liked = reader_id in channel.people_who_reacted(message_id, LIKE)
    disliked = reader_id in channel.people_who_reacted(message_id, DISLIKE)
    return VERDICTS[(liked, disliked)]
