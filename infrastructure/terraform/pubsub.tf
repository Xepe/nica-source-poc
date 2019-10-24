resource "google_pubsub_topic" "dataflow-job-topic" {
  name = "dataflow-job-topic"
}

# resource "google_pubsub_subscription" "dataflow-job-topic-subscription" {
#   name  = "dataflow-job-topic-subscription"
#   topic = "${google_pubsub_topic.dataflow-job-topic.name}"

#   ack_deadline_seconds = 20

#   push_config {
#     push_endpoint = "${google_cloudfunctions_function.dataflow-function}"

#     # attributes {
#     #   x-goog-version = "v1"
#     # }
#   }
# }



