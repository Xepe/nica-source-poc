# Cloud Function
resource "google_cloudfunctions_function" "trigger-pipeline-template-function" {
  count       = length(var.regions)
  project     = var.data_project
  region      = lookup(var.regions[count.index], "region")
  name        = "trigger-pipeline-template-function-${lookup(var.regions[count.index], "name")}"
  description = "Trigger pipeline template execution in dataflow to read data from database in project: ${var.main_project} then write data to BigQuery and DataStorage in project: ${var.data_project}"
  runtime     = "nodejs8"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.code-bucket.name
  source_archive_object = google_storage_bucket_object.trigger-function-zip.name
  trigger_http          = true
  entry_point           = "executeTemplateInDataflow"

  depends_on = [google_project_service.cloud-function-service]
}


# post_dataflow_processing_function
resource "google_cloudfunctions_function" "post-dataflow-processing" {
    count           = length(var.regions)
    project         = "var.data_project
    region          = lookup(var.regions[count.index], "region")
    name            = "post_dataflow_processing"
    description     = "Execute post processing actions after pipeline execution"
    runtime         = "python37"

    available_memory_mb   = 256
    source_archive_bucket = "${google_storage_bucket.code_bucket.name}"
    source_archive_object = "${google_storage_bucket_object.post_dataflow_processing_zip.name}"
    event_trigger {
        event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
        resource = "projects/${var.service_project}/topics/${google_pubsub_topic.post_dataflow_processing_topic.name}"
    }

    entry_point           = "main"
    timeout               = 540

    depends_on = [google_project_service.cloud-function-service, google_storage_bucket_object.post_dataflow_processing_zip]
}