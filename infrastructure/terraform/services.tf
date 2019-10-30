# Enable Dataflow API
resource "google_project_service" "dataflow-service" {
  project = "${var.processing_data_project}"
  service   = "dataflow.googleapis.com"
  disable_dependent_services = true
}

# Enable Cloud Function API
resource "google_project_service" "cloud-function-service" {
  project = "${var.processing_data_project}"
  service   = "cloudfunctions.googleapis.com"
  disable_dependent_services = true
}

# Enable Cloud Scheduler API
resource "google_project_service" "cloud-scheduler-service" {
  project = "${var.processing_data_project}"
  service   = "cloudscheduler.googleapis.com"
  disable_dependent_services = true
}