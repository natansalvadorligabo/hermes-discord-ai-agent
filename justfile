# The repo's commands; `just` lists them. Tools come from mise.toml (`mise install`).
#
# The agent runs as a Docker container on a VM in AWS or GCP. Everything it knows is in
# /srv/hermes on the VM, so moving it between clouds is stopping it, streaming that directory to
# the other VM, and starting it there. Only one VM may run it at a time, or the Radar posts twice.

set shell := ["bash", "-euo", "pipefail", "-c"]

key := env("HERMES_VM_KEY", home_directory() / ".ssh" / "hermes-vm")
image := "ghcr.io/natansalvadorligabo/hermes-discord-ai-agent"
stack := "/opt/hermes-stack"

[private]
default:
    @just --list

# Everything CI runs: format, lint, types, tests, Terraform
check:
    uv run ruff format --check .
    uv run ruff check .
    uv run mypy
    uv run pytest -q
    terraform fmt -recursive -check infra
    for cloud in aws gcp; do terraform -chdir=infra/$cloud init -backend=false -input=false >/dev/null && terraform -chdir=infra/$cloud validate -no-color >/dev/null; done
    just --fmt --check --unstable

# Build the agent's image locally, as CI does
build:
    docker build -t {{ image }}:dev .

# The ssh and scp options for a cloud's VM
[private]
ssh-options cloud:
    @echo "-i {{ key }} -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=infra/{{ cloud }}/.known_hosts"

# user@host of a cloud's VM, from its Terraform outputs
[private]
address cloud:
    @echo "$(terraform -chdir=infra/{{ cloud }} output -raw user)@$(terraform -chdir=infra/{{ cloud }} output -raw host)"

# Read the VM's current IP into Terraform's state without changing anything. GCP's IP changes
# after each nightly stop; AWS's does not, and refreshing it is harmless.
refresh cloud:
    terraform -chdir=infra/{{ cloud }} apply -refresh-only -auto-approve -input=false >/dev/null

# Run a command on a cloud's VM, or open a shell there (after `just refresh` if its IP moved).
# The command is quoted whole, so `;` and `|` in it run on the VM, not here.
ssh cloud *command:
    ssh $(just ssh-options {{ cloud }}) "$(just address {{ cloud }})" {{ if command == "" { "" } else { quote(command) } }}

# Create a cloud's VM and wait for its first boot to install Docker
up cloud:
    terraform -chdir=infra/{{ cloud }} init -input=false >/dev/null
    terraform -chdir=infra/{{ cloud }} apply
    rm -f infra/{{ cloud }}/.known_hosts
    until just ssh {{ cloud }} true 2>/dev/null; do sleep 10; done
    just ssh {{ cloud }} cloud-init status --wait

# Copy compose.yaml and prompts/ to a cloud's VM, pull the image and (re)start the agent
deploy cloud: (refresh cloud)
    scp -r $(just ssh-options {{ cloud }}) compose.yaml prompts "$(just address {{ cloud }}):{{ stack }}/"
    just ssh {{ cloud }} "cd {{ stack }} && sudo docker compose pull -q && sudo docker compose up -d"
    just ssh {{ cloud }} sudo docker exec hermes hermes gateway status

# Stop the agent on one cloud's VM and start it, with all it knows, on the other's
move from to: (refresh from) (refresh to)
    just ssh {{ from }} "cd {{ stack }} && sudo docker compose down"
    just ssh {{ from }} sudo tar -C /srv -czf - hermes | just ssh {{ to }} sudo tar -C /srv -xzf -
    just deploy {{ to }}

# Create the other cloud's VM, move the agent there, destroy the old VM
switch from to:
    just up {{ to }}
    just move {{ from }} {{ to }}
    just down {{ from }}

# Save a cloud's /srv/hermes under infra/.state-backups, then destroy its VM
down cloud: (refresh cloud)
    mkdir -p infra/.state-backups
    just ssh {{ cloud }} sudo tar -C /srv -czf - hermes > "infra/.state-backups/{{ cloud }}-$(date +%Y%m%d-%H%M%S).tgz"
    terraform -chdir=infra/{{ cloud }} destroy
    rm -f infra/{{ cloud }}/.known_hosts

# Follow the agent's logs on a cloud's VM
logs cloud: (refresh cloud)
    just ssh {{ cloud }} sudo docker logs -f --tail 100 hermes
