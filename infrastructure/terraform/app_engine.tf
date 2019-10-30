resource "google_app_engine_application" "app" {
  project     = "${var.processing_data_project}"
  location_id = "${var.app_engine_region}"
}