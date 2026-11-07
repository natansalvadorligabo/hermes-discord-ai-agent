"""`discord-agent`: the commands the Hermes skills run. Wires the Radar domain to its adapters.

Commands the agent reads print JSON; `jobs commands` prints shell lines for a person to run.
Errors go to stderr as JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from agent.adapters.config_files import DEFAULT_SOURCES, ConfigError, load_jobs, load_sources
from agent.adapters.discord import RestDiscordChannel
from agent.adapters.home import AgentHome
from agent.adapters.http import HttpError, HttpxClient
from agent.adapters.radar_store import JsonRadarStore
from agent.radar.feedback import sync_verdicts
from agent.radar.lead import collect_leads
from agent.radar.pick import RadarDraft, RadarError
from agent.radar.posting import post_radar

REPO_ROOT = Path(__file__).resolve().parents[2]
Command = Callable[[argparse.Namespace, AgentHome], object]


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point, e.g. `discord-agent radar leads --since-hours 36`."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    command: Command = args.command
    try:
        output = command(args, AgentHome.from_environment())
    except (ConfigError, HttpError, RadarError, MissingSetting, OSError) as error:
        print(json.dumps({"error": str(error), "kind": type(error).__name__}), file=sys.stderr)
        return 1
    if isinstance(output, str):
        print(output)
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="discord-agent", description=__doc__)
    groups = root.add_subparsers(required=True)

    home = groups.add_parser("home", help="where this Reader's files live")
    home.set_defaults(command=show_home)

    sources = groups.add_parser("sources", help="the Sources the Radar reads").add_subparsers(
        required=True
    )
    sources.add_parser("init", help="copy the starting Sources to the agent home").set_defaults(
        command=init_sources
    )

    radar = groups.add_parser("radar", help="build and post the Radar").add_subparsers(
        required=True
    )
    leads = radar.add_parser("leads", help="recent Leads never posted before")
    leads.add_argument("--since-hours", type=int, default=36)
    leads.set_defaults(command=show_leads)
    post = radar.add_parser("post", help="post a draft to the Radar channel")
    post.add_argument("draft", type=Path, help="JSON file: {intro, picks: [{title, url, ...}]}")
    post.set_defaults(command=post_draft)
    feedback = radar.add_parser("feedback", help="read 👍/👎 on recent Picks into Verdicts")
    feedback.add_argument("--window-days", type=int, default=14)
    feedback.set_defaults(command=show_feedback)

    jobs = groups.add_parser("jobs", help="the Jobs Hermes runs").add_subparsers(required=True)
    commands = jobs.add_parser("commands", help="print the hermes commands that install the Jobs")
    commands.add_argument("--workdir", type=Path, default=REPO_ROOT)
    commands.set_defaults(command=show_job_commands)
    return root


def show_home(_: argparse.Namespace, home: AgentHome) -> object:
    return {
        "root": home.root,
        "reader_profile": home.reader_profile,
        "reader_profile_exists": home.reader_profile.exists(),
        "sources": home.sources if home.sources.exists() else DEFAULT_SOURCES,
        "radar_store": home.radar_store,
        "drafts": home.drafts,
    }


def init_sources(_: argparse.Namespace, home: AgentHome) -> object:
    if home.sources.exists():
        return {"sources": home.sources, "created": False}
    home.root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DEFAULT_SOURCES, home.sources)
    return {"sources": home.sources, "created": True}


def show_leads(args: argparse.Namespace, home: AgentHome) -> object:
    since = datetime.now(UTC) - timedelta(hours=args.since_hours)
    sources_file = home.sources if home.sources.exists() else DEFAULT_SOURCES
    sources = load_sources(sources_file, HttpxClient())
    report = collect_leads(sources, since, JsonRadarStore(home.radar_store).posted_urls())
    return {
        "since": since.isoformat(),
        "leads": [asdict(lead) for lead in report.leads],
        "failures": [asdict(failure) for failure in report.failures],
    }


def post_draft(args: argparse.Namespace, home: AgentHome) -> object:
    draft = RadarDraft.from_json(json.loads(args.draft.read_text(encoding="utf-8")))
    posted = post_radar(draft, date.today(), radar_channel(), JsonRadarStore(home.radar_store))
    return {"posted": [asdict(pick) for pick in posted]}


def show_feedback(args: argparse.Namespace, home: AgentHome) -> object:
    store = JsonRadarStore(home.radar_store)
    changes = sync_verdicts(store, radar_channel(), date.today(), args.window_days)
    return {
        "changes": [
            {
                "title": change.pick.title,
                "url": change.pick.url,
                "topics": change.pick.topics,
                "posted_on": change.pick.posted_on,
                "previous": change.previous,
                "verdict": change.verdict,
            }
            for change in changes
        ]
    }


def show_job_commands(args: argparse.Namespace, _: AgentHome) -> object:
    jobs = load_jobs(REPO_ROOT / "jobs")
    return "\n".join(shlex.join(job.hermes_cron_create(args.workdir)) for job in jobs)


def radar_channel() -> RestDiscordChannel:
    return RestDiscordChannel(
        channel_id=required_setting("DISCORD_RADAR_CHANNEL_ID"),
        bot_token=required_setting("DISCORD_BOT_TOKEN"),
        http=HttpxClient(),
    )


def required_setting(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingSetting(
            f"expected the environment variable {name} to be set; "
            "add it to the Hermes .env and to terminal.env_passthrough"
        )
    return value


class MissingSetting(Exception):
    pass


if __name__ == "__main__":
    raise SystemExit(main())
