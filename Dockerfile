# The agent's image: the official Hermes image plus this repo's skills, Jobs and the
# discord-agent CLI the skills call. Every machine that runs the agent runs this image; what
# differs between machines is only the data volume mounted at /opt/data.
FROM nousresearch/hermes-agent:v0.23.0

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv

# Hermes' own tree (/opt/hermes) is read-only at runtime; this repo sits beside it, at the path
# skills.external_dirs points to. An editable install keeps `jobs/` next to the CLI's code.
WORKDIR /opt/hermes-discord-ai-agent
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY jobs ./jobs
COPY skills ./skills
ENV UV_PROJECT_ENVIRONMENT=/opt/discord-agent \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev --no-cache \
    && ln -s /opt/discord-agent/bin/discord-agent /usr/local/bin/discord-agent \
    && discord-agent --help >/dev/null

# Root on purpose: the image's entrypoint (s6-overlay) starts as root and drops to the hermes
# user itself.
WORKDIR /opt/hermes
