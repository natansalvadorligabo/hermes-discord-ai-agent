---
name: daily-radar
description: Radar run. Use when the daily-radar Job fires or the Reader asks for a Radar now.
version: 0.2.0
required_environment_variables:
  - name: RADAR_BOT_TOKEN
    prompt: Discord bot token for posting the Radar
    help: The bot's token, stored under this name too; Hermes keeps DISCORD_BOT_TOKEN for the gateway only.
    required_for: posting the Radar and reading reactions
  - name: RADAR_CHANNEL_ID
    prompt: ID of the Discord channel the Radar is posted to
    help: Enable Developer Mode in Discord, right-click the channel, Copy Channel ID.
    required_for: posting the Radar and reading reactions
  - name: RADAR_READER_ID
    prompt: The Reader's Discord user ID
    help: Right-click your own name with Developer Mode on, Copy User ID. Only these reactions count.
    required_for: reading reactions
metadata:
  hermes:
    category: personal
    tags: [radar, news, discord]
    requires_toolsets: [terminal]
---

# Daily Radar

Settings reach `discord-agent` only through the environment. When it reports a missing setting, end the run and name that setting in your final answer.

You are the Reader's editor. A Pick earns its place when the Reader would act on it this week: try it, change a decision, or bring it to their team. Every Pick is _actionable_ for this Reader, in light of their Reader profile.

## 1. Read the Reader profile

Run `discord-agent home` and read the file at `reader_profile`. When `reader_profile_exists` is false, end the run here: your final answer asks the Reader to start the reader interview.

Done when you can say, in one sentence each, what the Reader wants more of, what they skip, and what they learned from feedback.

## 2. Learn from recent Verdicts

Run `discord-agent radar feedback`. It lists every Pick from the last two weeks the Reader reacted to; `new` marks Verdicts since the last run. Apply the `radar-feedback` skill to the whole list.

Done when the radar-feedback skill's own completion line holds, or the list was empty.

## 3. Gather Leads

Run `discord-agent radar leads`. It covers the time since the last Radar and leaves out every link already posted. Note any `failures` for your final answer.

If web search is available and an interest under `Wants more of` has no Lead, run one search for news on it since the `since` timestamp and keep only primary sources: the announcement, the repo, the paper, the author's post.

Done when you have the Lead list and know which interests it leaves uncovered.

## 4. Choose the Picks

Pick the number the profile asks for (5 if it says nothing):

- Rank by _actionable_ for this Reader, then by how new the information is.
- One Pick per story: when several Leads cover the same news, keep the primary source.
- Leave out everything matching `Skip` or a lesson under `Learned from feedback`.
- Include at least one Pick the Reader can try in under an hour.

Open each chosen link and read it; write why it matters from what the page says.

Done when every Pick's link has been opened and its claim checked against the page.

## 5. Write the draft

Save this JSON to `<drafts>/<YYYY-MM-DD>.json` (`drafts` comes from `discord-agent home`):

```json
{
  "title": "Applied AI Radar · Mon, Nov 9",
  "intro": "One line on today's theme.",
  "footer": "React 👍 or 👎 on each pick, or reply with what you want.",
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

Write every field in the language the profile names, in plain words; `title` carries today's date. `why_it_matters` speaks to this Reader's situation (their stack, their team, their goals) in at most 600 characters. `topics` are short lowercase tags that the radar-feedback skill learns from.

Done when the file is saved and every Pick has all four fields.

## 6. Post

Run `discord-agent radar post <draft path>`. When it reports a message over the length limit or a missing field, fix the draft and run it once more.

Done when the command prints the posted titles.

## 7. Report

Your final answer is the run log: how many Picks were posted, their titles, any lessons added to the profile, and any Source failures.

Done when the log names every Source failure from step 3.
