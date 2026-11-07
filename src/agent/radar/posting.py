"""Posting a Radar: header, one message per Pick, like/dislike buttons, then remember the links."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from agent.radar.channel import DISLIKE, LIKE, MESSAGE_LIMIT, Channel
from agent.radar.lead import canonical_url
from agent.radar.pick import PostedPick, RadarDraft, RadarError
from agent.radar.store import RadarStore


@dataclass(frozen=True)
class Messages:
    """A Radar laid out as Discord messages: the header first, then one per Pick."""

    header: str
    picks: list[str] = field(default_factory=list)


def post_radar(
    draft: RadarDraft, day: date, channel: Channel, store: RadarStore
) -> list[PostedPick]:
    """Post the draft as the Radar for `day` and record every Pick in the store.

    Every message is checked against Discord's limit first: a Radar posts whole or not at all.
    Example: `post_radar(RadarDraft.from_json(raw), date.today(), channel, store)`
    """
    messages = lay_out(draft, day)
    channel.send_message(messages.header)
    posted: list[PostedPick] = []
    for pick, content in zip(draft.picks, messages.picks, strict=True):
        message = channel.send_message(content)
        channel.add_reaction(message.message_id, LIKE)
        channel.add_reaction(message.message_id, DISLIKE)
        posted.append(
            PostedPick(
                title=pick.title,
                url=canonical_url(pick.url),
                message_id=message.message_id,
                posted_on=day,
                topics=pick.topics,
            )
        )
    store.record(posted)
    return posted


def lay_out(draft: RadarDraft, day: date) -> Messages:
    messages = Messages(
        header=draft.header(day),
        picks=[pick.as_message(number) for number, pick in enumerate(draft.picks, start=1)],
    )
    if len(messages.header) > MESSAGE_LIMIT:
        raise RadarError(f"the header has {len(messages.header)} characters, limit {MESSAGE_LIMIT}")
    for number, content in enumerate(messages.picks, start=1):
        if len(content) > MESSAGE_LIMIT:
            raise RadarError(f"Pick {number} has {len(content)} characters, limit {MESSAGE_LIMIT}")
    return messages
