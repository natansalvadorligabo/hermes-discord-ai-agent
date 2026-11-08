# AGENTS.md

A Hermes Agent setup: three skills in `skills/` plus the `discord-agent` CLI they run, shipped together as one Docker image over the official Hermes one. The agent's personality is `prompts/SOUL.md`, mounted read-only where Hermes reads its identity (`$HERMES_HOME/SOUL.md`); text the model reads lives in `prompts/`. `README.md` covers setup; `GLOSSARY.md` is the domain language, used the same way in code, skills and docs.

## Layers

```
src/agent/
  radar/      domain: Lead, Pick, Draft, Verdict, the rules, and the ports (Channel, RadarStore, Source)
  jobs/       domain: Job and the hermes command it becomes
  adapters/   infrastructure: httpx, feedparser, PyYAML, the Discord REST API, files on disk
  cli.py      wiring: builds adapters and calls the domain; no rules live here
Dockerfile, compose.yaml  the image and how a VM runs it; all state in the data volume
infra/
  aws/, gcp/  one Terraform root per cloud, each with outputs `host` and `user`
  cloud-init.yaml.tftpl   the first boot both clouds share: a login user and Docker
justfile      every command: checks, image build, VM lifecycle, moving the agent (docs/adr/0002),
              deploying by hand (docs/adr/0003)
```

`radar/` and `jobs/` import nothing from `adapters/` or `cli.py`. Each third-party library appears in exactly one adapter file (`http.py`, `feeds.py`, `config_files.py`). Handlers in `cli.py` are named for what they do: commands (`post_draft`, `sync_feedback`) change state, queries (`recent_leads`, `home_paths`) only read. A new Job is a `jobs/*.yaml` file plus, if it needs one, a skill in `skills/`; a new domain gets its own folder beside `radar/`.

The Radar is posted by the CLI, not by Hermes delivery, because Hermes does not pass Discord reactions on: see `docs/adr/0001`.

## Commands

Run everything on Linux (WSL on Windows); `mise install` installs the tools pinned in `mise.toml`. Commands live in the `justfile`, not in shell scripts.

```sh
just check                     # everything CI runs, Terraform included
uv run pytest tests/test_x.py  # one file
uv run mypy                    # strict, src and tests
```

Tests sit at these seams, with doubles from `tests/fakes.py`:

- `collect_leads` and `leads_window_start`, with real feed parsing behind `FakeHttpClient`.
- `post_radar` and `read_verdicts`, with `FakeChannel` and a real `JsonRadarStore` in `tmp_path`.
- `RestDiscordChannel`, for rate limits and reaction parsing.
- `Job.hermes_cron_create`, which must match the flags Hermes accepts.

## Skills

Skills follow the agentskills.io format Hermes reads. Each step ends on a "Done when" line; keep them checkable. The Reader's data never goes in the repo: skills find it through `discord-agent home`.
