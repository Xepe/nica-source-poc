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
    project = "${var.data_project}"
}

# A service project gains access to network resources provided by its associated host project.
resource "google_compute_shared_vpc_service_project" "data" {
    host_project    = "${var.data_project}"
    service_project = "${var.processing_data_project}"
    depends_on = [google_compute_shared_vpc_host_project.main]
}

resource "google_compute_subnetwork_iam_member" "subnet" {
  project = "${var.data_project}"
  region = "${var.network_region}"
  subnetwork = "${var.data_project_sub_network}"
  role       = "roles/compute.networkUser"
  member     = "serviceAccount:service-1022478287302@dataflow-service-producer-prod.iam.gserviceaccount.com"
  depends_on = [google_compute_shared_vpc_host_project.main, google_project_service.dataflow-service]
}