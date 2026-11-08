variable "region" {
  type    = string
  default = "us-east-1" # cheapest; the bot does not care about latency
}

variable "instance_type" {
  type    = string
  default = "t3.small" # 2 GB RAM, about US$15/month
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

variable "budget_email" {
  type        = string
  default     = null
  description = "Where to send the budget alert. No budget is created when unset."
}

variable "monthly_budget_usd" {
  type    = number
  default = 20
}
