# This is the BigQuery dataset where the main data warehouse will be hosted
resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = "${var.dest_dataset}"
  friendly_name               = "${var.dest_dataset}"
  description                 = "Taxfyle main data warehouse dataset"
  default_table_expiration_ms = 3600000
}