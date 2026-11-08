# The Hermes VM on AWS: one EC2 instance in the default VPC, reachable only by SSH from your IP.
# Its contract with the justfile is the outputs in outputs.tf, the same as infra/gcp.

terraform {
  required_version = ">= 1.9"
  required_providers {
    aws  = { source = "hashicorp/aws", version = "~> 6.0" }
    http = { source = "hashicorp/http", version = "~> 3.4" }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = "hermes-discord-ai-agent" }
  }
}

data "http" "my_ip" {
  url = "https://checkip.amazonaws.com"
}

locals {
  ssh_cidr = coalesce(var.ssh_cidr, "${chomp(data.http.my_ip.response_body)}/32")
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-resolute-26.04-amd64-server-*"]
  }
}

resource "aws_security_group" "hermes" {
  name        = "hermes"
  description = "SSH from the operator; the Discord bot only connects out"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [local.ssh_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "hermes" }
}

resource "aws_instance" "hermes" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.hermes.id]

  user_data = templatefile("${path.module}/../cloud-init.yaml.tftpl", {
    ssh_public_key = trimspace(file(pathexpand(var.ssh_public_key_path)))
  })

  # t3 defaults to "unlimited", which bills for CPU bursts past the credit balance.
  credit_specification {
    cpu_credits = "standard"
  }

  metadata_options {
    http_tokens = "required" # IMDSv2 only
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  tags = { Name = "hermes" }

  # A new user_data would rebuild the VM and lose its state; rebuild on purpose with -replace.
  lifecycle {
    ignore_changes = [user_data, ami]
  }
}

resource "aws_budgets_budget" "monthly" {
  count        = var.budget_email == null ? 0 : 1
  name         = "hermes-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_email]
  }
}
