# main project
#resource "google_compute_network" "vpc_network" {
#    name = "${var.shared_vpc_network}" 
#    project = "${var.main_project}"
#    routing_mode = "REGIONAL"
#    auto_create_subnetworks = false    
#}

#resource "google_compute_subnetwork" "vpc-subnetwork" {
#   name = "${var.shared_vpc_sub_network}"  
#   project = "${var.main_project}"  
#   network = "${var.shared_vpc_network}"     
#   ip_cidr_range = "${var.shared_vpc_sub_network_ip_range}"
#   region = "${var.shared_vpc_sub_network_region}"
#   depends_on = [google_compute_network.vpc_network]
#}


# First approach 

#  Shared VPC (Concept)
#  https://cloud.google.com/vpc/docs/shared-vpc#iam_in_shared_vpc

# Setting_up_shred vpc (Setting rights)
#  https://cloud.google.com/vpc/docs/provisioning-shared-vpc#setting_up_shared_vpc
  
#  An Organization Admin can grant one or more IAM members the "Shared VPC Admin" and "Project IAM Admin" roles. 
#  The Project IAM Admin role grants Shared VPC Admins permission to share all existing and future subnets, 
#  not just individual subnets. This grant creates a binding at the organization or folder level, not the project level. 
#  So the IAM members must be defined in the organization, not just a project therein.

# When the user doesn't have the "Shared VPC Admin" role in host project you will receive this error:
# Error: Error enabling Shared VPC Host "project-name": googleapi: Error 403: Required 'compute.organizations.enableXpnHost' permission for 'projects/project-name', forbidden


# Enables the Google Compute Engine Shared VPC feature for the host project, assigning it as a Shared VPC host project.

# A host project provides network resources to associated service projects.
resource "google_compute_shared_vpc_host_project" "main" {
   project = "${var.main_project}"
}

# A service project gains access to network resources provided by its associated host project.
resource "google_compute_shared_vpc_service_project" "data" {
  host_project    = "${var.main_project}"
  service_project = "${var.data_project}"
  depends_on = [google_compute_shared_vpc_host_project.main]
}

# Second approach
# VPC Network (concept)
# https://cloud.google.com/vpc/docs/vpc-peering

#resource "google_compute_network" "vpc-network-main" {
#  project = "${var.main_project}"
#  name    = "vpc-network-main"
#  auto_create_subnetworks = "false"
#}

#resource "google_compute_subnetwork" "vpc-subnetwork-main" {
#  project = "${var.main_project}"
#  name          = "vpc-subnetwork-main"
#  ip_cidr_range = "10.16.0.0/16"
#  region        = "${var.shared_vpc_sub_network_region}"
#  network       = "${google_compute_network.vpc-network-main.self_link}"  
#  depends_on = [google_compute_network.vpc-network-main]
#}

#resource "google_compute_network" "vpc-network-data" {
#  project = "${var.data_project}"
#  name    = "vpc-network-data"
#  auto_create_subnetworks = "false"
#}

#resource "google_compute_subnetwork" "vpc-subnetwork-data" {
#  project = "${var.data_project}"
#  name          = "vpc-subnetwork-data"
#  ip_cidr_range = "10.17.0.0/16"
#  region        = "${var.shared_vpc_sub_network_region}"
#  network       = "${google_compute_network.vpc-network-data.self_link}"  
#  depends_on = [google_compute_network.vpc-network-data]
#}

#resource "google_compute_network_peering" "peering-main-project" {
#  name = "peering-main-project"
#  network = "${google_compute_network.vpc-network-main.self_link}"
#  peer_network = "${google_compute_network.vpc-network-data.self_link}"
#  depends_on = [google_compute_network.vpc-network-main, google_compute_network.vpc-network-data]
#}

#resource "google_compute_network_peering" "peering-data-project" {
#  name = "peering-data-project"
#  network = "${google_compute_network.vpc-network-data.self_link}"
#  peer_network = "${google_compute_network.vpc-network-main.self_link}"
#  depends_on = [google_compute_network.vpc-network-main, google_compute_network.vpc-network-data]
#}
