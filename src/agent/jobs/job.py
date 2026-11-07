"""Jobs: routines the agent runs on a schedule, kept as files to reinstall anywhere."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Job:
    name: str
    schedule: str
    prompt: str
    skills: tuple[str, ...]
    deliver: str
    timezone: str = ""

    def hermes_cron_create(self, workdir: Path) -> list[str]:
        """The `hermes cron create` command that installs this Job, as an argument list.

        Example: `shlex.join(job.hermes_cron_create(workdir=Path.cwd()))`
        """
        command = ["hermes", "cron", "create", self.schedule, self.prompt, "--name", self.name]
        for skill in self.skills:
            command += ["--skill", skill]
        command += ["--deliver", self.deliver, "--workdir", str(workdir)]
        if self.timezone:
            command += ["--timezone", self.timezone]
        return command
