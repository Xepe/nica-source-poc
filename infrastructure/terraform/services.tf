resource "google_project_service" "dataflow-service" {
  project = "${var.data_project}"
  service   = "dataflow.googleapis.com"
  disable_dependent_services = true
}

#resource "google_project_service" "compute-service" {
#  project = "${var.data_project}"
#  service = "compute.googleapis.com"
#  disable_dependent_services = false
#}
