# pubsub topics

#topic post-dataflow-processing-topic
resource "google_pubsub_topic" "post-dataflow-processing-topic" {
  name = "post-dataflow-processing-topic"  
}

#topic bq-error-importing-json-file
resource "google_pubsub_topic" "bq-error-importing-json-file" {
  name = "bq-error-importing-json-file"  
}