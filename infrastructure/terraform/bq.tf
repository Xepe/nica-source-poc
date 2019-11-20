# This is the BigQuery dataset where the main data warehouse will be hosted
resource "google_bigquery_dataset" "dataset" {
  count         = length(var.regions)
  dataset_id    = "${var.dest_dataset}-${lookup(var.regions[count.index], "name")}"
  friendly_name = "${var.dest_dataset}-${lookup(var.regions[count.index], "name")}"
  description   = "Taxfyle data warehouse dataset - ${lookup(var.regions[count.index], "name")}"
  location      = lookup(var.regions[count.index], "bigquery_dataset_location")
}
