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


# split_json_file_per_schema
locals {
    split_json_file_per_schema_filename = "split_json_file_per_schema_function_${substr(lower(replace(base64encode(data.archive_file.split-json-file-per-schema.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python split_json_file_per_schema folder
data "archive_file" "split-json-file-per-schema" {
  type        = "zip"
  source_dir = "./../../code/pubsub/split_json_file_per_schema"
  output_path = ".${replace(path.module, path.root, "")}/code/split_json_file_per_schema.zip"  
}

# Provisioning split_json_file_per_schema to bucket
resource "google_storage_bucket_object" "split-json-file-per-schema-zip" {
  name   = local.split_json_file_per_schema_filename
  source = ".${replace(path.module, path.root, "")}/code/split_json_file_per_schema.zip"
  bucket = "${google_storage_bucket.code-bucket.name}"
  depends_on = [google_storage_bucket.code-bucket]
}


