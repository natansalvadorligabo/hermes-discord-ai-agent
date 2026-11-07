"""Posting a Radar: header, one message per Pick, like/dislike buttons, then remember the links."""

from __future__ import annotations

from datetime import date

from agent.radar.channel import DISLIKE, LIKE, MESSAGE_LIMIT, Channel
from agent.radar.draft import DraftError, RadarDraft
from agent.radar.store import RadarStore


def post_radar(draft: RadarDraft, day: date, channel: Channel, store: RadarStore) -> None:
    """Post the draft as the Radar for `day` and record every Pick in the store.

    Every message is checked against Discord's limit first: a Radar posts whole or not at all.
    Example: `post_radar(RadarDraft.from_json(raw), date.today(), channel, store)`
    """
    header, *pick_messages = radar_messages(draft, day)
    channel.send_message(header)
    posted = []
    for pick, content in zip(draft.picks, pick_messages, strict=True):
        message_id = channel.send_message(content)
        channel.add_reaction(message_id, LIKE)
        channel.add_reaction(message_id, DISLIKE)
        posted.append(pick.posted_as(message_id, day))
    store.record(posted)


def radar_messages(draft: RadarDraft, day: date) -> list[str]:
    """The Radar as Discord messages: the header, then one per Pick, each within the limit.

    Example: `radar_messages(draft, date.today())` -> `["## Applied AI Radar ...", "**1. ..."]`
    """
    messages = [draft.header(day)] + [
        pick.as_message(number) for number, pick in enumerate(draft.picks, start=1)
    ]
    for index, content in enumerate(messages):
        if len(content) > MESSAGE_LIMIT:
            part = f"Pick {index}" if index else "The header"
            raise DraftError(f"{part} has {len(content)} characters, limit {MESSAGE_LIMIT}")
    return messages
