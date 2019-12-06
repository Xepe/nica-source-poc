resource "google_cloud_scheduler_job" "dataflow_trigger_full_load" {
  count     = length(var.regions)
  project   = var.data_project
  region    = lookup(var.regions[count.index], "region")
  name      = "dataflow-scheduler-full-load-job-${lookup(var.regions[count.index], "name")}"
  schedule  = "0 0 * * *"
  time_zone = "America/New_York"

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions_function.trigger-pipeline-template-function.*.https_trigger_url[count.index]

    body = base64encode(jsonencode(
      {
        parameters : {
          template_bucket = google_storage_bucket.code-bucket.name,
          network_region  = lookup(var.regions[count.index], "region"),
          etl_region      = lookup(var.regions[count.index], "name")
          full_load       = "True"
        }
      }
    ))
  }

  depends_on = [google_project_service.cloud-scheduler-service]
}

resource "google_cloud_scheduler_job" "dataflow_trigger_delta_load" {
  count     = length(var.regions)
  project   = var.data_project
  region    = lookup(var.regions[count.index], "region")
  name      = "dataflow-scheduler-delta-load-job-${lookup(var.regions[count.index], "name")}"
  schedule  = "0 6,12,18 * * *"
  time_zone = "America/New_York"

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions_function.trigger-pipeline-template-function.*.https_trigger_url[count.index]

    body = base64encode(jsonencode(
      {
        parameters : {
          template_bucket = google_storage_bucket.code-bucket.name,
          network_region  = lookup(var.regions[count.index], "region"),
          etl_region      = lookup(var.regions[count.index], "name")
          full_load       = "False"
        }
      }
    ))
  }

  depends_on = [google_project_service.cloud-scheduler-service]
}
