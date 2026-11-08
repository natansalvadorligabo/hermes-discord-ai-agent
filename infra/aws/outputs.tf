# The justfile reads only these; infra/gcp has the same two.

output "host" {
  value = aws_instance.hermes.public_ip
}

output "user" {
  value = "ops"
}
