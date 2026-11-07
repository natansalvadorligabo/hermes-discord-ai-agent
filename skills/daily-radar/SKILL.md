---
name: daily-radar
description: Build and post the Radar, the Reader's daily applied-AI news. Use when the daily-radar Job runs or the Reader asks for a Radar now.
version: 0.1.0
required_environment_variables:
  - name: DISCORD_BOT_TOKEN
    prompt: Discord bot token
    help: The same token the Hermes Discord gateway uses.
    required_for: posting the Radar and reading reactions
  - name: DISCORD_RADAR_CHANNEL_ID
    prompt: ID of the Discord channel the Radar is posted to
    help: Enable Developer Mode in Discord, right-click the channel, Copy Channel ID.
    required_for: posting the Radar and reading reactions
metadata:
  hermes:
    category: personal
    tags: [radar, news, discord]
    requires_toolsets: [terminal]
---

# Daily Radar

You are the Reader's editor. A Pick earns its place when the Reader would act on it this week: try it, change a decision, or bring it to their team. Every Pick is _actionable_ for this Reader, in light of their Reader profile.

## 1. Learn from the last Radars

Run `discord-agent radar feedback`. For each entry in `changes`, apply the `radar-feedback` skill.

Done when every change is reflected in the Reader profile, or the list was empty.

## 2. Read the Reader profile

Run `discord-agent home` and read the file at `reader_profile`. If `reader_profile_exists` is false, post nothing: your final answer tells the Reader to ask for the reader interview first.

Done when you can say, in one sentence each, what the Reader wants more of, what they skip, and what they learned from feedback.

## 3. Gather Leads

Run `discord-agent radar leads --since-hours 36` (on Mondays use `--since-hours 84` to cover the weekend). Note any `failures` for your final answer.

If web search is available and an interest under `Wants more of` has no Lead, run one search for news on it from the last two days and keep only primary sources (the announcement, the repo, the paper, the author's post).

Done when you have the Lead list and know which interests it leaves uncovered.

## 4. Choose the Picks

Pick the number the profile asks for (5 if it says nothing):

- Rank by _actionable_ for this Reader, then by how new the information is.
- One Pick per story: when several Leads cover the same news, keep the primary source.
- Leave out everything matching `Skip` or a lesson under `Learned from feedback`.
- Include at least one Pick the Reader can try in under an hour.

Open each chosen link and read it. Write why it matters from what the page says, so a release note you have not read never becomes a Pick.

Done when every Pick's link has been opened and its claim checked against the page.

## 5. Write the draft

Save this JSON to `<drafts>/<YYYY-MM-DD>.json` (`drafts` comes from `discord-agent home`):

```json
{
  "intro": "One line on today's theme.",
  "picks": [
    {
      "title": "Short, specific title",
      "url": "https://primary.source/link",
      "why_it_matters": "One to three sentences tied to the Reader's own work.",
      "topics": ["two", "or three"]
    }
  ]
}
```

Write in the language the profile names, in plain words. `why_it_matters` speaks to this Reader's situation (their stack, their team, their goals) in at most 600 characters. `topics` are short lowercase tags; the feedback skill learns from them.

Done when the file is saved and every Pick has all four fields.

## 6. Post

Run `discord-agent radar post <draft path>`. It posts the header and one message per Pick with 👍/👎 buttons, and remembers every link so it never comes back as a Lead. If it fails on a message length or a missing field, fix the draft and run it once more.

Done when the command prints the posted Picks.

## 7. Report

Your final answer is the run log: how many Picks were posted, their titles, and any Source failures.
