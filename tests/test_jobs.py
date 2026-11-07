from pathlib import Path

from agent.jobs.job import Job


def test_a_job_becomes_a_hermes_cron_create_command() -> None:
    job = Job(
        name="daily-radar",
        schedule="0 8 * * 1-5",
        prompt="Build today's Radar and post it.",
        skills=("daily-radar", "radar-feedback"),
        deliver="local",
        timezone="America/Sao_Paulo",
    )

    command = job.hermes_cron_create(workdir=Path("/home/reader/hermes-discord-ai-agent"))

    assert command == [
        "hermes", "cron", "create", "0 8 * * 1-5", "Build today's Radar and post it.",
        "--name", "daily-radar",
        "--skill", "daily-radar", "--skill", "radar-feedback",
        "--deliver", "local",
        "--workdir", str(Path("/home/reader/hermes-discord-ai-agent")),
        "--timezone", "America/Sao_Paulo",
    ]  # fmt: skip


def test_the_timezone_flag_is_left_out_so_the_hermes_profile_timezone_applies() -> None:
    job = Job(name="weekly", schedule="every monday 9am", prompt="p", skills=(), deliver="local")

    assert "--timezone" not in job.hermes_cron_create(workdir=Path("/repo"))
