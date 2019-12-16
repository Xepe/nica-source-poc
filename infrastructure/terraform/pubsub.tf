# pubsub topics

#topic bq-post-dataflow-processing-topic
resource "google_pubsub_topic" "bq-post-dataflow-processing-topic" {
  name = "bq-post-dataflow-processing"
}

#topic bq-error-importing-json-file-topic
resource "google_pubsub_topic" "bq-error-importing-json-file-topic" {
  name = "bq-error-importing-json-file"
}

#topic bq-create-views-and-cleanup-topic
resource "google_pubsub_topic" "bq-create-views-and-cleanup-topic" {
  name = "bq-create-views-and-cleanup"
}

#topic df-cleanup-topic
resource "google_pubsub_topic" "df-cleanup-topic" {
  name = "df-cleanup"
}