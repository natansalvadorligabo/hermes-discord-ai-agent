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


class ConfigError(Exception):
    pass


def load_sources(path: Path, http: HttpClient) -> list[Source]:
    """Every Source listed in a sources file, e.g. `load_sources(home.sources, HttpxClient())`."""
    entries = read_yaml(path).get("sources")
    if not isinstance(entries, list):
        raise ConfigError(f"expected a 'sources' list in {path}")
    return [source_from(entry, http, path) for entry in entries]


def source_from(entry: object, http: HttpClient, path: Path) -> Source:
    if not isinstance(entry, Mapping):
        raise ConfigError(f"expected each source in {path} to be a mapping, got {entry!r}")
    name = str(entry.get("name", ""))
    if "feed" in entry:
        return FeedSource(name=name, url=str(entry["feed"]), http=http)
    if "hacker_news" in entry:
        return HackerNewsSource(
            name=name,
            query=str(entry["hacker_news"]),
            http=http,
            min_points=int(entry.get("min_points", 30)),
        )
    raise ConfigError(f"expected source {name!r} in {path} to have 'feed' or 'hacker_news'")


def load_jobs(folder: Path) -> list[Job]:
    """Every Job in a folder of `*.yaml` files, e.g. `load_jobs(repo / "jobs")`."""
    return [job_from(read_yaml(path), path) for path in sorted(folder.glob("*.yaml"))]


def job_from(raw: Mapping[str, object], path: Path) -> Job:
    skills = raw.get("skills", [])
    missing = [key for key in ("schedule", "prompt", "deliver") if not raw.get(key)]
    if missing or not isinstance(skills, list):
        raise ConfigError(f"expected {path} to have schedule, prompt, deliver and a skills list")
    return Job(
        name=str(raw.get("name", path.stem)),
        schedule=str(raw["schedule"]),
        prompt=" ".join(str(raw["prompt"]).split()),
        skills=tuple(str(skill) for skill in skills),
        deliver=str(raw["deliver"]),
        timezone=str(raw.get("timezone", "")),
    )


def read_yaml(path: Path) -> Mapping[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ConfigError(f"expected {path} to hold a YAML mapping, got {type(raw).__name__}")
    return raw
