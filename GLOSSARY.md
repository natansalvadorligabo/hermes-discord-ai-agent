# Hermes Discord AI Agent

A Hermes Agent setup that learns what one person cares about and runs scheduled jobs for them on Discord. The first job is the daily Radar.

## People and preferences

**Reader**:
The one person the agent works for and writes the Radar to.
_Avoid_: User, subscriber, audience

**Reader profile**:
What the agent knows about the Reader: their work, interests, career direction, what to skip, and what it has learned from Feedback.
_Avoid_: Preferences, settings, persona

**Interview**:
The conversation in which the agent asks the Reader open questions and writes the first Reader profile.
_Avoid_: Onboarding, survey, setup

## The Radar

**Radar**:
A daily post of applied-AI news picked for the Reader, made of a header and one message per Pick.
_Avoid_: Digest, newsletter, brief, report

**Radar channel**:
The Discord channel where the Radar is posted and where the Reader reacts and replies.
_Avoid_: Feed, home channel

**Source**:
A place the agent looks for news: a feed or a Hacker News search.
_Avoid_: Provider, channel, origin

**Lead**:
A recent link a Source returned that has never been posted in a Radar.
_Avoid_: Candidate, item, article, story

**Draft**:
The Radar as the agent wrote it, before it is posted.
_Avoid_: Preview, proposal

**Pick**:
A Lead the agent chose for a Radar, with why it matters to the Reader.
_Avoid_: Highlight, selection, entry

**Verdict**:
The Reader's judgment of a posted Pick, read from their own reactions only: liked, disliked, mixed, or none yet.
_Avoid_: Rating, score, vote

**Feedback**:
Anything the Reader tells the agent about Picks: Verdicts from reactions and replies written in the channel.
_Avoid_: Signals, input

## Running

**Job**:
Something the agent does on a schedule, such as the daily Radar.
_Avoid_: Task, routine, cron
