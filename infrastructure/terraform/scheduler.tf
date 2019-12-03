resource "google_cloud_scheduler_job" "dataflow_trigger" {
  count     = length(var.regions)
  project   = var.data_project
  region    = lookup(var.regions[count.index], "region")
  name      = "dataflow-scheduler-job-${lookup(var.regions[count.index], "name")}"
  schedule  = "0 */6 * * *"
  time_zone = "America/New_York"

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions_function.trigger-pipeline-template-function.*.https_trigger_url[count.index]

    body = base64encode(jsonencode(
      {
        parameters : {
          template_bucket = google_storage_bucket.code-bucket.name,
          network_region  = lookup(var.regions[count.index], "region"),
          etl_region      = lookup(var.regions[count.index], "bigquery_dataset_location")
        }
      }
    ))
  }

  depends_on = [google_project_service.cloud-scheduler-service]
}
