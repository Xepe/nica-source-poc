# pubsub topics

#topic bq-post-dataflow-processing-topic
resource "google_pubsub_topic" "bq-post-dataflow-processing-topic" {
  count = length(var.regions)
  name  = "bq-post-dataflow-processing-${lookup(var.regions[count.index], "name")}"
}

#topic bq-error-importing-json-file-topic
resource "google_pubsub_topic" "bq-error-importing-json-file-topic" {
  count = length(var.regions)
  name  = "bq-error-importing-json-file-${lookup(var.regions[count.index], "name")}"
}

#topic bq-create-views-and-cleanup-topic
resource "google_pubsub_topic" "bq-create-views-and-cleanup-topic" {
  count = length(var.regions)
  name  = "bq-create-views-and-cleanup-${lookup(var.regions[count.index], "name")}"
}

#topic df-cleanup-topic
resource "google_pubsub_topic" "df-cleanup-topic" {
  count = length(var.regions)
  name  = "df-cleanup-${lookup(var.regions[count.index], "name")}"
}