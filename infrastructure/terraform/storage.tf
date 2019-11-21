# Bucket for data
resource "google_storage_bucket" "datalake-bucket" {
  count         = length(var.regions)
  name          = "${var.data_project}-datalake-${lookup(var.regions[count.index], "name")}"
  project       = var.data_project
  location      = lookup(var.regions[count.index], "region")
  force_destroy = true
}

# Bucket for Python code
resource "google_storage_bucket" "code-bucket" {
  name          = "${var.data_project}-code"
  project       = var.data_project
  location      = "us-central1"
  force_destroy = true
}

locals {
    trigger_function_gcs_filename = "trigger_function_${substr(lower(replace(base64encode(data.archive_file.trigger-function.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python trigger_function folder
data "archive_file" "trigger-function" {
  type        = "zip"
  source_dir  = "./../../code/trigger_function"
  output_path = ".${replace(path.module, path.root, "")}/code/trigger_function.zip"
}

# Provisioning trigger to bucket
resource "google_storage_bucket_object" "trigger-function-zip" {
  name       = local.trigger_function_gcs_filename
  source     = data.archive_file.trigger-function.output_path
  bucket     = google_storage_bucket.code-bucket.name
}
