# One Terraform root per cloud, the agent in a container

The agent runs on one VM, on AWS or on GCP, and moving it should be one command. A single Terraform root with `count = var.cloud == "aws" ? 1 : 0` on each cloud's resources looks like that command, but one `apply` would destroy the old VM and create the new one in the same run: the agent's state lives on the old VM's disk and would be gone before anything copied it. Both providers would also need credentials on every run, even for the cloud not in use.

So `infra/aws` and `infra/gcp` are separate roots with their own state. They share the first boot (`infra/cloud-init.yaml.tftpl`: a login user and Docker) and the same outputs (`host`, `user`), and that pair is the contract the `justfile` relies on.

What runs on the VM is the repo's image (the official Hermes image plus the skills and `discord-agent`) through `compose.yaml`, with every piece of state in one directory, `/srv/hermes`, mounted at the image's `/opt/data`. That makes the VM disposable and the move simple: `just switch <from> <to>` creates the new VM, stops the container on the old one, streams `/srv/hermes` across with `tar` over SSH, starts it on the new one, and destroys the old VM. `just down` saves `/srv/hermes` locally before destroying, whatever happens.

## Consequences

- A third cloud is a new `infra/<cloud>` root with the same two outputs and the same cloud-init.
- The roots keep local state (`terraform.tfstate`, git-ignored). It holds no secrets: the bot token and API keys live in `/srv/hermes/.env` and travel only inside the SSH stream.
- Paths inside the container are the same on every machine (`/opt/hermes-discord-ai-agent/skills`, `/opt/data`), so Hermes' config moves between VMs unchanged.
- Upgrading Hermes is a new `FROM` tag in the `Dockerfile`; rolling back a VM is pinning `HERMES_IMAGE` to an earlier commit's image.
