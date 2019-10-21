# main project
# resource "google_compute_network" "vpc_network" {
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


# Enables the Google Compute Engine Shared VPC feature for a project, assigning it as a Shared VPC host project.

# When the vpc is shared in other project Require 'compute.organizations.enableXpnHost' permission for 'projects/cloud39-sandbox'

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