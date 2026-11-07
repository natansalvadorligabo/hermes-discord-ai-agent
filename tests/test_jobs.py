from pathlib import Path

from agent.jobs.job import Job

RADAR = Job(
    name="daily-radar",
    schedule="0 8 * * 1-5",
    prompt="Build the Radar for today and post it.",
    skills=("daily-radar", "radar-feedback"),
    deliver="local",
)


def test_a_job_becomes_a_hermes_cron_create_command() -> None:
    command = RADAR.hermes_cron_create(workdir=Path("/home/reader/agent"))

    assert command == [
        "hermes", "cron", "create", "0 8 * * 1-5", "Build the Radar for today and post it.",
        "--name", "daily-radar",
        "--skill", "daily-radar", "--skill", "radar-feedback",
        "--deliver", "local",
        "--workdir", str(Path("/home/reader/agent")),
    ]  # fmt: skip


def test_the_readers_own_time_replaces_the_jobs_schedule() -> None:
    command = RADAR.rescheduled("30 7 * * 1,3,5", "Europe/Lisbon").hermes_cron_create(Path("/a"))

    assert command[3] == "30 7 * * 1,3,5"
    assert command[-2:] == ["--timezone", "Europe/Lisbon"]
