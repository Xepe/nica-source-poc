resource "google_project_service" "dataflow-service" {
  project = "${var.data_project}"
  service   = "dataflow.googleapis.com"
}

resource "google_project_service" "compute-service" {
  project = "${var.data_project}"
  service = "compute.googleapis.com"
}
