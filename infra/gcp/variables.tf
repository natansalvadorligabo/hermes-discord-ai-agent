variable "project" {
  type        = string
  description = "The GCP project ID to create the VM in."
}

variable "region" {
  type    = string
  default = "us-central1" # Always Free covers only us-central1, us-west1 and us-east1
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "machine_type" {
  type    = string
  default = "e2-micro" # Always Free: 2 shared vCPUs, 1 GB RAM
}

variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/hermes-vm.pub"
}

variable "ssh_cidr" {
  type        = string
  default     = null
  description = "Who may SSH in. Defaults to your current public IP; re-apply when it changes."
}

variable "schedule_time_zone" {
  type        = string
  default     = "America/Sao_Paulo"
  description = "Time zone of the nightly stop (03:00 to 05:00)."
}

variable "billing_account" {
  type        = string
  default     = null
  description = "Billing account ID (XXXXXX-XXXXXX-XXXXXX) for the spend alert. No budget is created when unset."
}

