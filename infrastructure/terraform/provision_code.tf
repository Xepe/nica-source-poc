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
    bq_post_dataflow_processing_gcs_filename = "bq_post_dataflow_processing_function_${substr(lower(replace(base64encode(data.archive_file.bq-post-dataflow-processing.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python bq_post_dataflow_processing folder
data "archive_file" "bq-post-dataflow-processing" {
  type        = "zip"
  source_dir = "./../../code/pubsub/bq_post_dataflow_processing"
  output_path = ".${replace(path.module, path.root, "")}/code/bq_post_dataflow_processing.zip"  
}

# Provisioning bq_post_dataflow_processing to bucket
resource "google_storage_bucket_object" "bq-post-dataflow-processing-zip" {
  name   = local.bq_post_dataflow_processing_gcs_filename
  source = ".${replace(path.module, path.root, "")}/code/bq_post_dataflow_processing.zip"
  bucket = "${google_storage_bucket.code-bucket.name}"
  depends_on = [google_storage_bucket.code-bucket]
}


# notify_error_importing_json_file
locals {
    bq_notify_error_importing_json_file_filename = "bq_notify_error_importing_json_file_function_${substr(lower(replace(base64encode(data.archive_file.bq-notify-error-importing-json-file.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python bq_notify_error_importing_json_file folder
data "archive_file" "bq-notify-error-importing-json-file" {
  type        = "zip"
  source_dir = "./../../code/pubsub/bq_notify_error_importing_json_file"
  output_path = ".${replace(path.module, path.root, "")}/code/bq_notify_error_importing_json_file.zip"  
}

# Provisioning notify_error_importing_json_file to bucket
resource "google_storage_bucket_object" "bq-notify-error-importing-json-file-zip" {
  name   = local.bq_notify_error_importing_json_file_filename
  source = ".${replace(path.module, path.root, "")}/code/bq_notify_error_importing_json_file.zip"
  bucket = "${google_storage_bucket.code-bucket.name}"
  depends_on = [google_storage_bucket.code-bucket]
}


# bq_create_views_and_cleanup
locals {
    bq_create_views_and_cleanup_filename = "bq_create_views_and_cleanup_function_${substr(lower(replace(base64encode(data.archive_file.bq-create-views-and-cleanup.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python bq_create_views_and_cleanup folder
data "archive_file" "bq-create-views-and-cleanup" {
  type        = "zip"
  source_dir = "./../../code/pubsub/bq_create_views_and_cleanup"
  output_path = ".${replace(path.module, path.root, "")}/code/bq_create_views_and_cleanup.zip"  
}

# Provisioning bq_create_views_and_cleanup to bucket
resource "google_storage_bucket_object" "bq-create-views-and-cleanup-zip" {
  name   = local.bq_create_views_and_cleanup_filename
  source = ".${replace(path.module, path.root, "")}/code/bq_create_views_and_cleanup.zip"
  bucket = "${google_storage_bucket.code-bucket.name}"
  depends_on = [google_storage_bucket.code-bucket]
}

# df_cleanup
locals {
    df_cleanup_filename = "df_cleanup_function_${substr(lower(replace(base64encode(data.archive_file.df-cleanup.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python df_cleanup folder
data "archive_file" "df-cleanup" {
  type        = "zip"
  source_dir = "./../../code/pubsub/df_cleanup"
  output_path = ".${replace(path.module, path.root, "")}/code/df_cleanup.zip"  
}

# Provisioning df_cleanup to bucket
resource "google_storage_bucket_object" "df-cleanup-zip" {
  name   = local.df_cleanup_filename
  source = ".${replace(path.module, path.root, "")}/code/df_cleanup.zip"
  bucket = "${google_storage_bucket.code-bucket.name}"
  depends_on = [google_storage_bucket.code-bucket]
}