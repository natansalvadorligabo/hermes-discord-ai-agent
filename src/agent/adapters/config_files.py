"""YAML files the Reader edits: Sources and Jobs. PyYAML appears only in this file."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml

from agent.adapters.feeds import FeedSource, HackerNewsSource
from agent.adapters.http import HttpClient
from agent.jobs.job import Job
from agent.radar.lead import Source

DEFAULT_SOURCES = Path(__file__).with_name("default_sources.yaml")
JOB_KEYS = ("schedule", "prompt", "deliver")


class ConfigError(Exception):
    pass


def sources_file(own_sources: Path) -> Path:
    """The Reader's own sources file once it exists, the starting Sources until then.

    Example: `sources_file(home.sources)` -> `~/.discord-agent/sources.yaml`
    """
    return own_sources if own_sources.exists() else DEFAULT_SOURCES


def load_sources(path: Path, http: HttpClient) -> list[Source]:
    """Every Source listed in a sources file, e.g. `load_sources(path, HttpxClient())`."""
    entries = _read_yaml(path).get("sources")
    if not isinstance(entries, list):
        raise ConfigError(f"expected a 'sources' list in {path}, got {entries!r:.200}")
    return [_source_from(entry, http, path) for entry in entries]


def load_job(folder: Path, name: str) -> Job:
    """The Job in `<folder>/<name>.yaml`, e.g. `load_job(repo / "jobs", "daily-radar")`."""
    path = folder / f"{name}.yaml"
    if not path.exists():
        available = sorted(job.stem for job in folder.glob("*.yaml"))
        raise ConfigError(f"expected a Job named one of {available} in {folder}, got {name!r}")
    return _job_from(_read_yaml(path), path)


def _source_from(entry: object, http: HttpClient, path: Path) -> Source:
    if not isinstance(entry, Mapping):
        raise ConfigError(f"expected each source in {path} to be a mapping, got {entry!r:.200}")
    name = str(entry.get("name", ""))
    if "feed" in entry:
        return FeedSource(name=name, url=str(entry["feed"]), http=http)
    if "hacker_news" in entry:
        source = HackerNewsSource(name=name, query=str(entry["hacker_news"]), http=http)
        if "min_points" in entry:
            source.min_points = int(entry["min_points"])
        return source
    raise ConfigError(
        f"expected source {name!r} in {path} to have 'feed' or 'hacker_news', got {dict(entry)}"
    )


def _job_from(raw: Mapping[str, object], path: Path) -> Job:
    skills = raw.get("skills", [])
    missing = [key for key in JOB_KEYS if not raw.get(key)]
    if missing or not isinstance(skills, list):
        raise ConfigError(
            f"expected {path} to have {', '.join(JOB_KEYS)} and a skills list; "
            f"missing {missing}, skills {skills!r}"
        )
    return Job(
        name=str(raw.get("name", path.stem)),
        schedule=str(raw["schedule"]),
        prompt=" ".join(str(raw["prompt"]).split()),
        skills=tuple(str(skill) for skill in skills),
        deliver=str(raw["deliver"]),
        timezone=str(raw.get("timezone", "")),
    )


def _read_yaml(path: Path) -> Mapping[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ConfigError(f"expected {path} to hold a YAML mapping, got {type(raw).__name__}")
    return raw
