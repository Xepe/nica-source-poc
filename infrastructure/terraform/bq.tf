# This is the BigQuery dataset where the main data warehouse will be hosted
resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = "main_dwh"
  friendly_name               = "main_dwh"
  description                 = "Taxfyle main data warehouse dataset"
  default_table_expiration_ms = 3600000
}