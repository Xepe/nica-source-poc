# main project
resource "google_compute_network" "vpc_network" {
  project = $"{var.main_project}",
  name = $"{var.shared_vpc_network}",  
  routing_mode = "REGIONAL",
  auto_create_subnetworks = false
}