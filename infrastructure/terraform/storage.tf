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

  # provisioner "local-exec" {
  #   command = "python ./../../code/pipeline_df/main-df.py --runner DataflowRunner --project ${var.data_project} --service_account_email ${google_service_account.service-project-service-account-data-pipeline.email} --temp_location gs://${google_storage_bucket.datalake-bucket.name}/tmp --staging_location gs://${google_storage_bucket.code-bucket.name}/binaries --subnetwork https://www.googleapis.com/compute/v1/projects/${var.host_project}/regions/${var.network_region}/subnetworks/${var.host_project_sub_network} --region ${var.network_region} --requirements_file ./../../code/pipeline_df/requirements.txt --template_location gs://${google_storage_bucket.code-bucket.name}/templates/pipeline-template-${lower(lookup(var.regions[count.index], "name"))} --db_host ${var.db_host} --db_port ${var.db_port} --db_user ${var.db_user} --db_password '${var.db_password}' --dest_dataset ${var.dest_dataset} --dest_bucket ${google_storage_bucket.datalake-bucket.name} --etl_region ${lookup(var.regions[count.index], "name")}"
  # }
}

# Zip Python trigger_function folder
data "archive_file" "trigger-function" {
  type        = "zip"
  source_dir  = "./../../code/trigger_function"
  output_path = ".${replace(path.module, path.root, "")}/code/trigger_function.zip"
}

# Provisioning trigger to bucket
resource "google_storage_bucket_object" "trigger-function-zip" {
  name       = "trigger_function.zip"
  source     = ".${replace(path.module, path.root, "")}/code/trigger_function.zip"
  bucket     = google_storage_bucket.code-bucket.name
  depends_on = [google_storage_bucket.code-bucket]
}
