# The justfile reads only these; infra/aws has the same two.

output "host" {
  value = google_compute_instance.hermes.network_interface[0].access_config[0].nat_ip
}

output "user" {
  value = "ops"
}
