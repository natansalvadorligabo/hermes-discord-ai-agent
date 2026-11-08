# Deploy the image to the VM by hand, with `just deploy`

CI publishes a new image to GHCR on every push to main, but the VM only runs it when the operator runs `just deploy <cloud>`, which copies `compose.yaml` and `prompts/`, pulls the image and recreates the container. The two automatic alternatives were weighed and left out for now:

- **Push from CI** (a job that SSHes into the VM after publishing). SSH on the VM is open only to the operator's IP; letting GitHub's runners in means opening it to their whole address range, or a cloud-specific tunnel (AWS SSM, GCP IAP) that breaks the one-cloud-like-the-other contract of ADR 0002. It also needs the VM's address and an SSH key in GitHub secrets, and the address changes on every `switch` and, on GCP, every night.
- **Pull on the VM** (a timer running `docker compose pull && up -d`, Watchtower-style). It needs no open port and no secret, but it restarts the agent at moments nobody chose: in the middle of a conversation or of the 08:00 Radar. It also covers only the image; a change to `compose.yaml` or `prompts/SOUL.md` would still need a deploy, so there would be two ways in and the VM's state would be harder to reason about.

One person operates this agent and deploys a few times a month, so a deliberate deploy costs a minute and buys a known moment of change, a container that runs exactly what was last deployed, and a closed SSH port.

## Consequences

- A merge to main changes nothing in production until `just deploy`. The image that runs is the `:main` of the last deploy; `HERMES_IMAGE` pins an earlier commit's image to roll back.
- Personality and compose changes travel with the same command as image changes.
- Revisit when deploys become frequent, when more than one person ships, or when the agent can drain its work before a restart (then the pull timer is the natural next step, since it keeps SSH closed and works the same on every cloud).
