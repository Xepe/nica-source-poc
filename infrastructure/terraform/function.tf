# Cloud Function
# resource "google_cloudfunctions_function" "dataflow-function" {
#     project               = "${var.data_project}"
#     region                = "${var.network_region}"
#     name                  = "configure-dataflow"
#     description           = "Configure dataflow to read data from database in project: ${var.main_project} then write data to BigQuery and DataStorage in project: ${var.data_project}"
#     runtime               = "python37"

#     available_memory_mb   = 1024
#     source_archive_bucket = "${google_storage_bucket.code-bucket.name}"
#     source_archive_object = "${google_storage_bucket_object.application-zip.name}"
#     trigger_http          = true
#     entry_point           = "run"

#     depends_on = [google_project_service.cloud-function-service]
# }

resource "google_cloudfunctions_function" "dataflow-function" {
    project               = "${var.data_project}"
    region                = "${var.network_region}"
    name                  = "configure-dataflow"
    description           = "Configure dataflow to read data from database in project: ${var.main_project} then write data to BigQuery and DataStorage in project: ${var.data_project}"
    runtime               = "python37"    
    timeout               = 540

    available_memory_mb   = 1024
    source_archive_bucket = "${google_storage_bucket.code-bucket.name}"
    source_archive_object = "${google_storage_bucket_object.application-zip.name}"
    entry_point           = "run"

    event_trigger {
        event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
        resource = "projects/${var.data_project}/topics/${google_pubsub_topic.dataflow-job-topic.name}"       
    }

    depends_on = [google_project_service.cloud-function-service]
}