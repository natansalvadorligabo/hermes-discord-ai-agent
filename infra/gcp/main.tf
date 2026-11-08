# The Hermes VM on GCP: one Always Free e2-micro, reachable only by SSH from your IP.
# Its contract with the justfile is the outputs in outputs.tf, the same as infra/aws.

terraform {
  required_version = ">= 1.9"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 7.0" }
    http   = { source = "hashicorp/http", version = "~> 3.4" }
  }
}

provider "google" {
  project = var.project
  region  = var.region
  zone    = var.zone
}

data "http" "my_ip" {
  url = "https://checkip.amazonaws.com"
}

locals {
  ssh_cidr = coalesce(var.ssh_cidr, "${chomp(data.http.my_ip.response_body)}/32")
}

resource "google_compute_firewall" "hermes_ssh" {
  name          = "hermes-ssh"
  network       = "default"
  description   = "SSH from the operator; the Discord bot only connects out"
  source_ranges = [local.ssh_cidr]
  target_tags   = ["hermes"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_instance" "hermes" {
  name         = "hermes"
  machine_type = var.machine_type
  tags         = ["hermes"]
  labels       = { project = "hermes-discord-ai-agent" }

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2604-lts-amd64"
      size  = 30            # the Always Free limit
      type  = "pd-standard" # the only disk type Always Free covers
    }
  }

  network_interface {
    network = "default"
    access_config {} # ephemeral public IP
  }

  metadata = {
    user-data = templatefile("${path.module}/../cloud-init.yaml.tftpl", {
      ssh_public_key = trimspace(file(pathexpand(var.ssh_public_key_path)))
    })
  }

  shielded_instance_config {
    enable_secure_boot = true
  }

  # New user-data would rebuild the VM and lose its state; rebuild on purpose with -replace.
  lifecycle {
    ignore_changes = [metadata["user-data"], boot_disk[0].initialize_params[0].image]
  }
}
