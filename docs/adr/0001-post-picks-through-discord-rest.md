# Post Picks through the Discord REST API, not Hermes delivery

Hermes can deliver a cron Job's final answer to a Discord channel, but its gateway does not hand Discord reactions to the agent or to plugins (the community reaction plugin covers Telegram only). To learn from 👍/👎 per Pick, every Pick must be its own message whose ID we keep. So the `discord-agent radar post` command sends the Radar itself with the bot token, one message per Pick, records each message ID, and the Job delivers to `local`. Before each Radar, `discord-agent radar feedback` reads back, through the same API, who reacted to each recent Pick, and keeps only the Reader's reactions (`RADAR_READER_ID`).

## Consequences

- The bot token must reach the agent's terminal through `terminal.env_passthrough`. Hermes never passes `DISCORD_BOT_TOKEN` to tools (it is the gateway's own credential), so the CLI reads the same token as `RADAR_BOT_TOKEN`, and its other settings under the same `RADAR_` prefix, outside the `DISCORD_` names Hermes owns.
- If Hermes starts exposing Discord reactions, this command can go and the Job can deliver to `discord:#channel` again; the stored Verdicts stay valid.
