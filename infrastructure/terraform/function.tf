# Cloud Functions

# trigger_pipeline_template_function
resource "google_cloudfunctions_function" "trigger-pipeline-template-function" {
  count       = length(var.regions)
  project     = var.data_project
  region      = lookup(var.regions[count.index], "region")
  name        = "trigger-pipeline-template-${lookup(var.regions[count.index], "name")}"
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
resource "google_cloudfunctions_function" "bq-post-dataflow-processing-function" {
    count           = length(var.regions)
    project         = var.data_project
    region          = lookup(var.regions[count.index], "region")
    name            = "bq-post-dataflow-processing-${lookup(var.regions[count.index], "name")}"
    description     = "Execute post processing actions after pipeline execution"
    runtime         = "python37"

    available_memory_mb   = 512
    source_archive_bucket = "${google_storage_bucket.code-bucket.name}"
    source_archive_object = "${google_storage_bucket_object.bq-post-dataflow-processing-zip.name}"
    event_trigger {
        event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
        resource = "projects/${var.data_project}/topics/${google_pubsub_topic.bq-post-dataflow-processing-topic.name}"
    }

    entry_point           = "main"
    timeout               = 540

    depends_on = [google_project_service.cloud-function-service]
}

# notify_error_importing_json_file_to_bq_function
resource "google_cloudfunctions_function" "bq-notify-error-json-schema-function" {
    count           = length(var.regions)
    project         = var.data_project
    region          = lookup(var.regions[count.index], "region")
    name            = "bq-notify-error-json-schema-${lookup(var.regions[count.index], "name")}"
    description     = "Split a JSON file into several files per schema founds"
    runtime         = "python37"

    available_memory_mb   = 256
    source_archive_bucket = "${google_storage_bucket.code-bucket.name}"
    source_archive_object = "${google_storage_bucket_object.bq-notify-error-importing-json-file-zip.name}"
    event_trigger {
        event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
        resource = "projects/${var.data_project}/topics/${google_pubsub_topic.bq-error-importing-json-file-topic.name}"
    }

    entry_point           = "main"
    timeout               = 540

    depends_on = [google_project_service.cloud-function-service]
}

#  bq_create_views_and_cleanup_function
resource "google_cloudfunctions_function" "bq-create-views-and-cleanup-function" {
    count           = length(var.regions)
    project         = var.data_project
    region          = lookup(var.regions[count.index], "region")
    name            = "bq-create-views-and-cleanup-${lookup(var.regions[count.index], "name")}"
    description     = "BQ create view and cleanup"
    runtime         = "python37"

    available_memory_mb   = 256
    source_archive_bucket = "${google_storage_bucket.code-bucket.name}"
    source_archive_object = "${google_storage_bucket_object.bq-create-views-and-cleanup-zip.name}"
    event_trigger {
        event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
        resource = "projects/${var.data_project}/topics/${google_pubsub_topic.bq-create-views-and-cleanup-topic.name}"
    }

    entry_point           = "main"
    timeout               = 540

    depends_on = [google_project_service.cloud-function-service]
}

#  df_cleanup
resource "google_cloudfunctions_function" "df-cleanup-function" {
    count           = length(var.regions)
    project         = var.data_project
    region          = lookup(var.regions[count.index], "region")
    name            = "df-cleanup-${lookup(var.regions[count.index], "name")}"
    description     = "Cleanup Dataflow binaries"
    runtime         = "python37"

    available_memory_mb   = 256
    source_archive_bucket = "${google_storage_bucket.code-bucket.name}"
    source_archive_object = "${google_storage_bucket_object.df-cleanup-zip.name}"
    event_trigger {
        event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
        resource = "projects/${var.data_project}/topics/${google_pubsub_topic.df-cleanup-topic.name}"
    }

    entry_point           = "main"
    timeout               = 540

    depends_on = [google_project_service.cloud-function-service]
}