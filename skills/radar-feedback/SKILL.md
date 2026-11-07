---
name: radar-feedback
description: Radar feedback. Use when the Reader replies about a Pick or the Radar, or the daily-radar skill hands you the output of `discord-agent radar feedback`.
version: 0.2.0
metadata:
  hermes:
    category: personal
    tags: [radar, feedback, profile]
---

# Radar feedback

Feedback comes in two forms: Verdicts (the Reader's 👍/👎, listed by `discord-agent radar feedback` for the last two weeks) and replies the Reader writes in the Radar channel. Turn it into lessons in the Reader profile that change the next Radar.

Open the Reader profile at the `reader_profile` path from `discord-agent home`.

Done when you have the profile open and the Feedback in front of you.

## Weighing Feedback

- Words outrank reactions. A reply says why; a reaction only says yes or no.
- Read the Verdicts as a set: the _pattern_ is what the liked (or disliked) Picks share across `topics`, source, kind (release, paper, tutorial, opinion, launch) and depth. Two or more Verdicts that agree make a lesson; a reply makes one on its own.
- `mixed` Verdicts carry no lesson.
- Verdicts without `new` were already weighed once; they count toward a pattern, and a lesson already in the profile stays as written.

## Writing lessons

- Lessons go under `## Learned from feedback`, one per line, newest first, dated: `- 2026-11-07: More hands-on write-ups on agent sandboxes (👍 on 3 of 3).`
- When a new lesson extends an old one, merge them into one line with the newest date. When it contradicts an old one, replace the old line.
- Keep the section under 15 lines by merging the oldest related lessons.
- A reply that plainly changes a core section ("stop sending funding news", "I moved to the data team") is edited into that section (`Skip`, `Work`, ...).

Done when every reply is in the profile, and every pattern backed by two or more agreeing Verdicts is a lesson.

## Answering a reply

When the Reader wrote to you, answer in one line with what you changed in the profile, or with the question you need answered to change it.

Done when the Reader has that one line.
