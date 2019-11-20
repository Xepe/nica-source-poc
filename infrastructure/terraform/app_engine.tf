resource "google_app_engine_application" "app" {
  count       = length(var.regions)
  project     = var.data_project
  location_id = lookup(var.regions[count.index], "region")
}
