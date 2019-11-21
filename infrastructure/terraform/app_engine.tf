resource "google_app_engine_application" "app" {
  project     = var.data_project
  location_id = "us-central1"
}
