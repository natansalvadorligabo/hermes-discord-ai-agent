"""`discord-agent`: the commands the Hermes skills run. Wires the Radar domain to its adapters.

Commands print JSON for the agent to read, except `jobs command`, which prints a shell line.
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
from datetime import UTC, date, datetime
from pathlib import Path

from agent.adapters.config_files import (
    DEFAULT_SOURCES,
    ConfigError,
    load_job,
    load_sources,
    sources_file,
)
from agent.adapters.discord import RestDiscordChannel
from agent.adapters.home import AgentHome
from agent.adapters.http import HttpError, HttpxClient
from agent.adapters.radar_store import JsonRadarStore, StoreError
from agent.radar.draft import DraftError, RadarDraft
from agent.radar.feedback import VERDICT_WINDOW_DAYS, read_verdicts
from agent.radar.lead import collect_leads, leads_window_start
from agent.radar.pick import Verdict
from agent.radar.posting import post_radar

REPO_ROOT = Path(__file__).resolve().parents[2]
Handler = Callable[[argparse.Namespace, AgentHome], object]


class MissingSetting(Exception):
    pass


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point, e.g. `discord-agent radar leads`."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    handler: Handler = args.handler
    try:
        output = handler(args, AgentHome.from_environment())
    except (ConfigError, DraftError, HttpError, MissingSetting, StoreError, OSError) as error:
        print(json.dumps({"error": str(error), "kind": type(error).__name__}), file=sys.stderr)
        return 1
    print(output if isinstance(output, str) else json.dumps(output, indent=2, ensure_ascii=False))
    return 0


def parser() -> argparse.ArgumentParser:
    """The full command tree: `home`, `sources`, `radar` and `jobs`."""
    root = argparse.ArgumentParser(prog="discord-agent", description=__doc__)
    groups = root.add_subparsers(required=True)
    groups.add_parser("home", help="where this Reader's files live").set_defaults(
        handler=home_paths
    )
    sources = groups.add_parser("sources", help="the Sources the Radar reads")
    sources.add_subparsers(required=True).add_parser(
        "init", help="copy the starting Sources to the agent home"
    ).set_defaults(handler=init_sources)
    _add_radar_commands(groups.add_parser("radar", help="build and post the Radar"))
    _add_job_commands(groups.add_parser("jobs", help="the Jobs Hermes runs"))
    return root


def _add_radar_commands(radar: argparse.ArgumentParser) -> None:
    commands = radar.add_subparsers(required=True)
    commands.add_parser("leads", help="Leads since the last Radar").set_defaults(
        handler=recent_leads
    )
    post = commands.add_parser("post", help="post a draft to the Radar channel")
    post.add_argument("draft", type=Path, help="JSON file: {intro, picks: [{title, url, ...}]}")
    post.set_defaults(handler=post_draft)
    feedback = commands.add_parser("feedback", help="read the Reader's 👍/👎 into Verdicts")
    feedback.add_argument("--window-days", type=int, default=VERDICT_WINDOW_DAYS)
    feedback.set_defaults(handler=sync_feedback)


def _add_job_commands(jobs: argparse.ArgumentParser) -> None:
    command = jobs.add_subparsers(required=True).add_parser(
        "command", help="print the hermes command that installs a Job"
    )
    command.add_argument("name", help="a file name in jobs/, e.g. daily-radar")
    command.add_argument("--schedule", default="", help="cron expression, e.g. '0 8 * * 1-5'")
    command.add_argument("--timezone", default="", help="e.g. Europe/Lisbon")
    command.add_argument("--workdir", type=Path, default=REPO_ROOT)
    command.set_defaults(handler=job_command)


def home_paths(_: argparse.Namespace, home: AgentHome) -> object:
    """Paths the skills read and write, and whether the Reader profile exists yet."""
    return {
        "root": str(home.root),
        "reader_profile": str(home.reader_profile),
        "reader_profile_exists": home.reader_profile.exists(),
        "sources": str(sources_file(home.sources)),
        "radar_store": str(home.radar_store),
        "drafts": str(home.drafts),
    }


def init_sources(_: argparse.Namespace, home: AgentHome) -> object:
    """Copy the starting Sources into the agent home, keeping an existing file."""
    if home.sources.exists():
        return {"sources": str(home.sources), "created": False}
    home.root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DEFAULT_SOURCES, home.sources)
    return {"sources": str(home.sources), "created": True}


def recent_leads(_: argparse.Namespace, home: AgentHome) -> object:
    """Leads since the last Radar (36 hours to 7 days back), never posted before."""
    store = JsonRadarStore(home.radar_store)
    since = leads_window_start(datetime.now(UTC), store.last_radar_day())
    sources = load_sources(sources_file(home.sources), HttpxClient())
    report = collect_leads(sources, since, store.posted_urls())
    return {
        "since": since.isoformat(),
        "leads": [
            asdict(lead) | {"published_at": lead.published_at.isoformat()} for lead in report.leads
        ],
        "failures": [asdict(failure) for failure in report.failures],
    }


def post_draft(args: argparse.Namespace, home: AgentHome) -> object:
    """Post the draft file as today's Radar."""
    draft = RadarDraft.from_json(json.loads(args.draft.read_text(encoding="utf-8")))
    post_radar(draft, date.today(), _radar_channel(), JsonRadarStore(home.radar_store))
    return {"posted": [pick.title for pick in draft.picks]}


def sync_feedback(args: argparse.Namespace, home: AgentHome) -> object:
    """Save the Reader's latest Verdicts and list every recent Pick they reacted to."""
    store = JsonRadarStore(home.radar_store)
    readings = read_verdicts(
        store.posted_picks(),
        _radar_channel(),
        _required_setting("DISCORD_READER_ID"),
        date.today(),
        args.window_days,
    )
    store.save_verdicts({r.pick.message_id: r.verdict for r in readings if r.changed})
    return {
        "verdicts": [
            {
                "title": reading.pick.title,
                "url": reading.pick.url,
                "topics": list(reading.pick.topics),
                "posted_on": reading.pick.posted_on.isoformat(),
                "verdict": reading.verdict.value,
                "new": reading.changed,
            }
            for reading in readings
            if reading.verdict is not Verdict.NONE
        ]
    }


def job_command(args: argparse.Namespace, _: AgentHome) -> object:
    """The `hermes cron create` line for one Job, at the Reader's time when given."""
    job = load_job(REPO_ROOT / "jobs", args.name).rescheduled(args.schedule, args.timezone)
    return shlex.join(job.hermes_cron_create(args.workdir))


def _radar_channel() -> RestDiscordChannel:
    return RestDiscordChannel(
        channel_id=_required_setting("DISCORD_RADAR_CHANNEL_ID"),
        bot_token=_required_setting("DISCORD_BOT_TOKEN"),
        http=HttpxClient(),
    )


def _required_setting(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingSetting(
            f"expected the environment variable {name} to be set, got nothing; "
            "add it to the Hermes .env and to terminal.env_passthrough"
        )
    return value


if __name__ == "__main__":
    raise SystemExit(main())
