# Enable Dataflow API
resource "google_project_service" "dataflow-service" {
  project = "${var.service_project}"
  service   = "dataflow.googleapis.com"
  disable_on_destroy = false
}

# Enable Cloud Function API
resource "google_project_service" "cloud-function-service" {
  project = "${var.service_project}"
  service   = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

# Enable Cloud Scheduler API
resource "google_project_service" "cloud-scheduler-service" {
  project = "${var.service_project}"
  service   = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

# Enable Cloud Big Query
resource "google_project_service" "cloud-big-query-service" {
  project = "${var.service_project}"
  service   = "bigquery-json.googleapis.com"
  disable_on_destroy = false
}

# # Enable Cloud Storage
# resource "google_project_service" "cloud-storage-service" {
#   project = "${var.service_project}"
#   service   = "storage-component.googleapis.com"
#   disable_on_destroy = false
# }
