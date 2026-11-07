---
name: reader-interview
description: Interview the Reader and write their Reader profile. Use when the Reader sets up the Radar, asks to redo or review their profile, or says their work, goals or interests changed.
version: 0.1.0
metadata:
  hermes:
    category: personal
    tags: [radar, profile, onboarding]
---

# Reader interview

The Radar is only as good as the Reader profile behind it. You are a curious interviewer: open questions, one at a time, follow-ups on anything vague, and the Reader's own words in the profile.

## 1. Find the profile

Run `discord-agent home`. It prints `reader_profile` (the path) and `reader_profile_exists`.

- Profile exists: read it, show the Reader a short summary, and ask what changed. Interview only the areas they want to change; keep the rest as written.
- No profile: interview every area below.

Done when you know whether this is a first interview or an update, and which areas to cover.

## 2. Interview

Ask one question per message. When an answer is broad ("AI stuff", "backend"), follow up until you could tell a good Pick from a bad one for this person. Record only what the Reader said or confirmed; a job title, a company or one answer tells you nothing about the others, so ask.

Areas, matching the sections of [the template](templates/reader-profile.md):

- **Work**: their role, what they build or run day to day, their stack.
- **AI in their work**: how AI shows up in that work today, in their words.
- **Career direction**: where they want to be in a year or two, and what would help.
- **Learning now**: anything they are studying, formally or not. "Nothing right now" is a full answer.
- **Wants more of**: topics, kinds of content (releases, papers, tutorials, case studies, opinion) and examples of things they loved reading.
- **Skip**: what wastes their time.
- **Radar format**: Picks per Radar (suggest 5), language, how deep each Pick goes, which days and what time.
- **Trusted sources**: blogs, newsletters, people, repos they already follow.

Done when every section of the template has an answer or an explicit "none".

## 3. Write the profile

Fill [templates/reader-profile.md](templates/reader-profile.md) and save it at the `reader_profile` path. Keep `## Learned from feedback` as it was (empty on a first interview). Then send the Reader a short summary of what you wrote and apply their corrections.

Done when the Reader has confirmed the summary.

## 4. Tune the Sources

1. Run `discord-agent sources init`; it prints the sources file path.
2. Edit that file: add a `feed:` or `hacker_news:` entry for each trusted source and main interest; remove starting Sources that sit outside the Reader's interests. GitHub repos have release feeds at `https://github.com/<owner>/<repo>/releases.atom`.
3. Run `discord-agent radar leads --since-hours 72` and fix or drop every Source listed under `failures`.

Done when the leads command reports no failures and returns Leads that match the profile.

## 5. Schedule the Radar

Run `discord-agent jobs commands`. It prints the `hermes cron create` command for the daily Radar. Replace its schedule with the Reader's days and time as a cron expression (`0 8 * * 1-5` is 08:00 on weekdays), add `--timezone <Area/City>` if it differs from the Hermes config, and run it. Run `hermes cron list` and tell the Reader when the first Radar arrives.

Done when `hermes cron list` shows the `daily-radar` Job with the Reader's schedule.
