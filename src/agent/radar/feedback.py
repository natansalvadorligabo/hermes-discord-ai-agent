"""Feedback from reactions: turning 👍/👎 on posted Picks into Verdicts."""

from __future__ import annotations

from datetime import date, timedelta

from agent.radar.channel import DISLIKE, LIKE, Channel, Reaction
from agent.radar.pick import Verdict, VerdictChange
from agent.radar.store import RadarStore

VERDICT_WINDOW_DAYS = 14


def verdict_from(reactions: list[Reaction]) -> Verdict:
    """The Reader's Verdict on one Pick, ignoring the bot's own like/dislike buttons.

    Example: `verdict_from([Reaction("👍", count=2, includes_bot=True)])` -> `Verdict.LIKED`
    """
    people = {reaction.emoji: reaction.people for reaction in reactions}
    liked = people.get(LIKE, 0) > 0
    disliked = people.get(DISLIKE, 0) > 0
    if liked and disliked:
        return Verdict.MIXED
    if liked:
        return Verdict.LIKED
    if disliked:
        return Verdict.DISLIKED
    return Verdict.NONE


def sync_verdicts(
    store: RadarStore, channel: Channel, today: date, window_days: int = VERDICT_WINDOW_DAYS
) -> list[VerdictChange]:
    """Read reactions on Picks posted in the last `window_days`, save them, return what changed.

    Example: `sync_verdicts(store, channel, today=date.today())` -> `[VerdictChange(...)]`
    """
    oldest = today - timedelta(days=window_days)
    recent = [pick for pick in store.posted_picks() if pick.posted_on >= oldest]
    changes = []
    for pick in recent:
        verdict = verdict_from(channel.reactions_on(pick.message_id))
        if verdict is not pick.verdict:
            changes.append(VerdictChange(pick=pick, previous=pick.verdict, verdict=verdict))
    store.save_verdicts({change.pick.message_id: change.verdict for change in changes})
    return changes
