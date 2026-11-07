---
name: radar-feedback
description: Learn from the Reader's Feedback on the Radar and update their Reader profile. Use when the Reader replies about a Pick or the Radar, or when `discord-agent radar feedback` reports Verdict changes.
version: 0.1.0
metadata:
  hermes:
    category: personal
    tags: [radar, feedback, profile]
---

# Radar feedback

Feedback comes in two forms: Verdicts (👍/👎 reactions, read by `discord-agent radar feedback`) and replies the Reader writes in the Radar channel. Your job is to turn it into lessons in the Reader profile that change the next Radar.

Run `discord-agent home` and open the file at `reader_profile`.

## Weighing Feedback

- Words outrank reactions. A reply says why; a reaction only says yes or no.
- A single Verdict is weak evidence. Look for the _pattern_ behind it: what the Picks share across `topics`, source, kind (release, paper, tutorial, opinion, launch) and depth. Write a lesson when two or more Verdicts agree, or when the Reader says it in words.
- `mixed` and `none` Verdicts carry no lesson.

## Writing lessons

- Lessons go under `## Learned from feedback`, one per line, newest first, dated: `- 2026-11-07: More hands-on write-ups on agent sandboxes (👍 on 3 of 3).`
- When a new lesson extends an old one, merge them into one line with the newest date. When it contradicts an old one, replace the old line.
- Keep the section under 15 lines by merging the oldest related lessons.
- A reply that plainly changes a core section ("stop sending funding news", "I moved to the data team") is edited into that section (`Skip`, `Work`, ...) instead.

Done when every Verdict change or reply is either a lesson, an edit to a section, or judged too weak to write.

## Answering a reply

When the Reader wrote to you, answer in one line with what you changed in the profile, or with the question you need answered to change it.
