# The Hermes VM on GCP: one Free Tier e2-micro, reachable only by SSH from your IP.
# Its contract with the justfile is the outputs in outputs.tf, the same as infra/aws.
#
# Everything here stays inside the Free Tier, checked against Google's Cloud Billing Catalog:
# - e2-micro in us-central1, us-west1 or us-east1: free for one instance all month.
# - 30 GB pd-standard boot disk: "Storage PD Capacity" is free up to 30 GiB-month.
# - Ephemeral external IPv4: "External IP Charge on a Standard VM" is free for the first 721
#   hours a month, and a 31-day month has 744. The VM stops two hours every night (the
#   schedule below) so it runs at most ~700 hours. No static IP: it bills while the VM is off.

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
  # The budget API bills its quota to a project; with user credentials it must be named.
  billing_project       = var.project
  user_project_override = true
}

data "http" "my_ip" {
  url = "https://checkip.amazonaws.com"
}

data "google_project" "this" {}

locals {
  ssh_cidr = coalesce(var.ssh_cidr, "${chomp(data.http.my_ip.response_body)}/32")
}

resource "google_project_service" "apis" {
  for_each           = toset(["compute.googleapis.com", "billingbudgets.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
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

  depends_on = [google_project_service.apis]
}

# Keeps the external IP under its 721 free hours a month. Google allows up to 15 minutes of delay
# on each scheduled start and stop, so two hours off leaves at least 1.5 a night.
resource "google_compute_resource_policy" "nightly_stop" {
  name   = "hermes-nightly-stop"
  region = var.region
  instance_schedule_policy {
    vm_stop_schedule {
      schedule = "0 3 * * *"
    }
    vm_start_schedule {
      schedule = "0 5 * * *"
    }
    time_zone = var.schedule_time_zone
  }

  depends_on = [google_project_service.apis]
}

# The schedule runs as the Compute Engine service agent, which needs leave to stop and start VMs.
resource "google_project_iam_member" "scheduler_can_start_stop" {
  project = var.project
  role    = "roles/compute.instanceAdmin.v1"
  member  = "serviceAccount:service-${data.google_project.this.number}@compute-system.iam.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

resource "google_compute_instance" "hermes" {
  name              = "hermes"
  machine_type      = var.machine_type
  tags              = ["hermes"]
  labels            = { project = "hermes-discord-ai-agent" }
  resource_policies = [google_compute_resource_policy.nightly_stop.id]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2604-lts-amd64"
      size  = 30            # the Free Tier limit
      type  = "pd-standard" # the only disk type the Free Tier covers; the console defaults to balanced
    }
  }

  network_interface {
    network = "default"
    access_config {} # ephemeral public IP: it changes after each nightly stop
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

  depends_on = [google_project_iam_member.scheduler_can_start_stop]
}

# Emails the billing account's admins at the first cent spent, should anything leave the Free Tier.
resource "google_billing_budget" "free_tier_guard" {
  count           = var.billing_account == null ? 0 : 1
  billing_account = var.billing_account
  display_name    = "hermes-free-tier-guard"

  budget_filter {
    projects = ["projects/${data.google_project.this.number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = "1"
    }
  }

  threshold_rules {
    threshold_percent = 0.01 # US$0.01
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  depends_on = [google_project_service.apis]
}
