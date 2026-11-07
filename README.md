# Hermes Discord AI Agent

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) setup that interviews you about your work and goals, then posts a daily **Radar** of applied-AI news to a Discord channel and learns from your 👍/👎 and your replies.

The Radar is the first Job; the agent is meant to take on more routines over time.

## How it works

```
                 ┌───────────── Hermes Agent ─────────────┐
 08:00 cron ───▶ │ daily-radar skill                      │
                 │  1. discord-agent radar feedback  ◀────┼──── 👍/👎 on past Picks
                 │  2. read your Reader profile           │
                 │  3. discord-agent radar leads   ◀──────┼──── feeds, GitHub releases, Hacker News
                 │  4. pick, open and read each link      │
                 │  5. discord-agent radar post  ─────────┼───▶ #radar: header + one message per Pick
                 └────────────────────────────────────────┘
 your reply in #radar ───▶ radar-feedback skill ───▶ Reader profile
```

- **Hermes** does the thinking, the scheduling and the conversation on Discord.
- **Three skills** (`skills/`) tell it how: `reader-interview`, `daily-radar`, `radar-feedback`.
- **`discord-agent`**, a small Python CLI, does the deterministic parts: collecting Leads, posting the Radar, reading reactions back. Each Pick is its own message so a reaction belongs to one Pick ([why the CLI posts instead of Hermes](docs/adr/0001-post-picks-through-discord-rest.md)).
- **Your data** lives outside the repo, in `~/.discord-agent/` (or `$DISCORD_AGENT_HOME`): `reader-profile.md`, `sources.yaml`, `radar.json`.

The words used here (Reader, Lead, Pick, Verdict...) are defined in [GLOSSARY.md](GLOSSARY.md).

## Setup

You need [uv](https://docs.astral.sh/uv/), Hermes Agent and a Discord server you manage.

### 1. Install Hermes and this repo

```sh
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash   # Windows: iex (irm https://hermes-agent.nousresearch.com/install.ps1)
git clone https://github.com/natansalvadorligabo/hermes-discord-ai-agent
cd hermes-discord-ai-agent
uv tool install --editable .     # puts `discord-agent` on your PATH
```

### 2. Create the Discord bot

1. In the [Developer Portal](https://discord.com/developers/applications), create an application and a bot. Turn on the **Message Content** and **Server Members** intents.
2. Invite it with the recommended permissions: `https://discord.com/oauth2/authorize?client_id=<APP_ID>&scope=bot+applications.commands&permissions=309237763136`
3. Create the Radar channel (e.g. `#radar`) and copy its ID (Developer Mode, right-click, Copy Channel ID).

Add to the Hermes `.env` (`~/.hermes/.env`, or `%LOCALAPPDATA%\hermes\.env` on Windows):

```sh
DISCORD_BOT_TOKEN=...
DISCORD_ALLOWED_USERS=<your Discord user ID>
DISCORD_HOME_CHANNEL=<Radar channel ID>
DISCORD_RADAR_CHANNEL_ID=<Radar channel ID>
```

### 3. Point Hermes at the skills

In the Hermes `config.yaml`:

```yaml
timezone: America/New_York            # yours

skills:
  external_dirs:
    - /path/to/hermes-discord-ai-agent/skills

terminal:
  env_passthrough:                    # lets `discord-agent` post and read reactions
    - DISCORD_BOT_TOKEN
    - DISCORD_RADAR_CHANNEL_ID

discord:
  free_response_channels: ["<Radar channel ID>"]     # reply without @-mentioning the bot
  channel_prompts:
    "<Radar channel ID>": >
      This is the Radar channel. When the Reader writes about a Pick or the Radar,
      use the radar-feedback skill.
```

Start the gateway: `hermes gateway install` (or `hermes gateway` in the foreground).

### 4. Get interviewed

Message the bot: _"Interview me for my Radar."_ The `reader-interview` skill asks about your work, goals, what you are learning, what to skip and how you want the Radar, writes your Reader profile, tunes your Sources and schedules the `daily-radar` Job.

To schedule it by hand instead: `discord-agent jobs commands` prints the `hermes cron create` command from [`jobs/daily-radar.yaml`](jobs/daily-radar.yaml).

## Teaching it

- **React** 👍 or 👎 on a Pick. Before the next Radar, the agent reads the reactions and writes what it learned under `## Learned from feedback` in your profile.
- **Reply** in the Radar channel (_"more like #3"_, _"skip funding rounds"_). Words weigh more than reactions.
- **Edit** `~/.discord-agent/reader-profile.md` or `sources.yaml` yourself at any time; they are plain files.

## Commands

| Command | What it does |
| --- | --- |
| `discord-agent home` | Where your profile, Sources and Radar store live |
| `discord-agent sources init` | Copy the starting Sources to your home so you can edit them |
| `discord-agent radar leads [--since-hours 36]` | Recent Leads never posted before, as JSON |
| `discord-agent radar post <draft.json>` | Post a Radar draft to the Radar channel |
| `discord-agent radar feedback [--window-days 14]` | Read 👍/👎 on recent Picks and report the Verdicts that changed |
| `discord-agent jobs commands` | Print the `hermes cron create` commands for `jobs/*.yaml` |

## Develop

```sh
uv sync
sh scripts/check.sh   # ruff format, ruff check, mypy --strict, pytest
```

Contributor and agent notes are in [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE)
