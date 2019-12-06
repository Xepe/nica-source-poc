# -----------------------------------  http cloud functions  --------------------------------------------------------

locals {
    trigger_pipeline_template_gcs_filename = "trigger_pipeline_template_${substr(lower(replace(base64encode(data.archive_file.trigger-pipeline-template.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python trigger_pipeline_template folder
data "archive_file" "trigger-pipeline-template" {
  type        = "zip"
  source_dir  = "./../../code/http/trigger_pipeline_template"
  output_path = ".${replace(path.module, path.root, "")}/code/trigger_pipeline_template.zip"
}

# Provisioning trigger to bucket
resource "google_storage_bucket_object" "trigger-pipeline-template-zip" {
  name       = local.trigger_pipeline_template_gcs_filename
  source     = data.archive_file.trigger-pipeline-template.output_path
  bucket     = google_storage_bucket.code-bucket.name
}

# ------------------------------------- pubsub cloud functions ------------------------------------------------------

# post_dataflow_processing
locals {
    post_dataflow_processing_gcs_filename = "post_dataflow_processing_function_${substr(lower(replace(base64encode(data.archive_file.post-dataflow-processing.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python post_dataflow_processing folder
data "archive_file" "post-dataflow-processing" {
  type        = "zip"
  source_dir = "./../../code/pubsub/post_dataflow_processing"
  output_path = ".${replace(path.module, path.root, "")}/code/post_dataflow_processing.zip"  
}

# Provisioning post_dataflow_processing to bucket
resource "google_storage_bucket_object" "post-dataflow-processing-zip" {
  name   = local.post_dataflow_processing_gcs_filename
  source = ".${replace(path.module, path.root, "")}/code/post_dataflow_processing.zip"
  bucket = "${google_storage_bucket.code-bucket.name}"
  depends_on = [google_storage_bucket.code-bucket]
}


# notify_error_importing_json_file_to_bq
locals {
    notify_error_importing_json_file_to_bq_filename = "notify_error_importing_json_file_to_bq_function_${substr(lower(replace(base64encode(data.archive_file.notify-error-importing-json-file-to-bq.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python notify_error_importing_json_file_to_bq folder
data "archive_file" "notify-error-importing-json-file-to-bq" {
  type        = "zip"
  source_dir = "./../../code/pubsub/notify_error_importing_json_file_to_bq"
  output_path = ".${replace(path.module, path.root, "")}/code/notify_error_importing_json_file_to_bq.zip"  
}

# Provisioning notify_error_importing_json_file_to_bq to bucket
resource "google_storage_bucket_object" "notify-error-importing-json-file-to-bq-zip" {
  name   = local.notify_error_importing_json_file_to_bq_filename
  source = ".${replace(path.module, path.root, "")}/code/notify_error_importing_json_file_to_bq.zip"
  bucket = "${google_storage_bucket.code-bucket.name}"
  depends_on = [google_storage_bucket.code-bucket]
}


# bq_refresh_table_view
locals {
    bq_refresh_table_view_filename = "bq_refresh_table_view_function_${substr(lower(replace(base64encode(data.archive_file.bq-refresh-table-view.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python bq_refresh_table_view folder
data "archive_file" "bq-refresh-table-view" {
  type        = "zip"
  source_dir = "./../../code/pubsub/bq_refresh_table_view"
  output_path = ".${replace(path.module, path.root, "")}/code/bq_refresh_table_view.zip"  
}

# Provisioning bq_refresh_table_view to bucket
resource "google_storage_bucket_object" "bq-refresh-table-view-zip" {
  name   = local.bq_refresh_table_view_filename
  source = ".${replace(path.module, path.root, "")}/code/bq_refresh_table_view.zip"
  bucket = "${google_storage_bucket.code-bucket.name}"
  depends_on = [google_storage_bucket.code-bucket]
}
