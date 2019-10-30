# Cloud Function
resource "google_cloudfunctions_function" "trigger-pipeline-template-function" {
    project               = "${var.processing_data_project}"
    region                = "${var.network_region}"
    name                  = "trigger-pipeline-template-function"
    description           = "Trigger pipeline template execution in dataflow to read data from database in project: ${var.data_project} then write data to BigQuery and DataStorage in project: ${var.processing_data_project}"
    runtime               = "nodejs8"

    available_memory_mb   = 256
    source_archive_bucket = "${google_storage_bucket.code-bucket.name}"
    source_archive_object = "${google_storage_bucket_object.trigger-function-zip.name}"
    trigger_http          = true
    entry_point           = "executeTemplateInDataflow"

    depends_on = [google_project_service.cloud-function-service]
}