# Cloud Functions

# trigger-pipeline-template-function
resource "google_cloudfunctions_function" "trigger-pipeline-template-function" {
  count       = length(var.regions)
  project     = var.data_project
  region      = lookup(var.regions[count.index], "region")
  name        = "trigger-pipeline-template-function-${lookup(var.regions[count.index], "name")}"
  description = "Trigger pipeline template execution in dataflow to read data from database in project: ${var.main_project} then write data to BigQuery and DataStorage in project: ${var.data_project}"
  runtime     = "nodejs8"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.code-bucket.name
  source_archive_object = google_storage_bucket_object.trigger-pipeline-template-zip.name
  trigger_http          = true
  entry_point           = "executeTemplateInDataflow"

  depends_on = [google_project_service.cloud-function-service]
}


# post_dataflow_processing_function
resource "google_cloudfunctions_function" "post-dataflow-processing-function" {
    count           = length(var.regions)
    project         = var.data_project
    region          = lookup(var.regions[count.index], "region")
    name            = "post-dataflow-processing-function-${lookup(var.regions[count.index], "name")}"
    description     = "Execute post processing actions after pipeline execution"
    runtime         = "python37"

    available_memory_mb   = 256
    source_archive_bucket = "${google_storage_bucket.code-bucket.name}"
    source_archive_object = "${google_storage_bucket_object.post-dataflow-processing-zip.name}"
    event_trigger {
        event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
        resource = "projects/${var.data_project}/topics/${google_pubsub_topic.post-dataflow-processing-topic.name}"
    }

    entry_point           = "main"
    timeout               = 540

    depends_on = [google_project_service.cloud-function-service]
}

# split_json_file_per_schema_function
resource "google_cloudfunctions_function" "split-json-file-per-schema-function" {
    count           = length(var.regions)
    project         = var.data_project
    region          = lookup(var.regions[count.index], "region")
    name            = "split-json-file-per-schema-function-${lookup(var.regions[count.index], "name")}"
    description     = "Split a JSON file into several files per schema founds"
    runtime         = "python37"

    available_memory_mb   = 256
    source_archive_bucket = "${google_storage_bucket.code-bucket.name}"
    source_archive_object = "${google_storage_bucket_object.split-json-file-per-schema-zip.name}"
    event_trigger {
        event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
        resource = "projects/${var.data_project}/topics/${google_pubsub_topic.bq-error-importing-json-file.name}"
    }

    entry_point           = "main"
    timeout               = 540

    depends_on = [google_project_service.cloud-function-service]
}