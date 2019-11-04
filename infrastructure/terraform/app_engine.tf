resource "google_app_engine_application" "app" {
  project     = "${var.service_project}"
  location_id = "${var.service_project_app_engine_location_id}"
}