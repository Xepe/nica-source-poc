resource "google_cloud_scheduler_job" "dataflow_trigger" {
project = "${var.processing_data_project}"
region  = "${var.network_region}"
name    = "dataflow-scheduler-job"
schedule = "0 */4 * * *"
time_zone = "${var.timezone}"

http_target {
    http_method = "POST"
    uri = "${google_cloudfunctions_function.trigger-pipeline-template-function.https_trigger_url}" 
    body = "${base64encode(jsonencode(
        {    
            parameters: {
                template_buquet = "${google_storage_bucket.code-bucket.name}",
                template_name = "",
                region = "${var.network_region}"
            }    
        }
    ))}" 
}
depends_on = [google_project_service.cloud-scheduler-service]
}

