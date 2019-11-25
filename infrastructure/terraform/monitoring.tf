# Create notification channel
resource "google_monitoring_notification_channel" "basic" {
    project = var.data_project
    display_name = "Email Notification Channel"
    type = "email"
    labels = {
        email_address = var.notification_email
    }
}

# Create monitoring alert policy
resource "google_monitoring_alert_policy" "alert_policy-job-fail" {
  display_name = "Failed DataFlow Job"
  combiner = "OR"
  conditions {
    display_name = "trigger-pipeline-template job execution"
    condition_threshold {
      filter = "metric.type=\"dataflow.googleapis.com/job/is_failed\" AND resource.type=\"dataflow_job\""
      duration = "900s"
      comparison = "COMPARISON_GT" 
      threshold_value = 0         
    }
  }  
  notification_channels = [
      "${google_monitoring_notification_channel.basic.name}"
  ]
}
