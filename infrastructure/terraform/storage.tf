# This is the Google Cloud Storage where the data lake will be created
resource "google_storage_bucket" "datalake-bucket" {
    name    = "${var.data_project}-datalake"
    project = "${var.data_project}"
}

# Bucket for terraform etl-tfstate
resource "google_storage_bucket" "etl-tfstate-bucket" {
    name    = "${var.data_project}-da-data-etl-tfstate"
    project = "${var.data_project}"
}