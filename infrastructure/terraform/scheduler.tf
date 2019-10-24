#resource "google_cloud_scheduler_job" "dataflow_trigger" {
# project = "${var.data_project}"
# region  = "${var.network_region}"
# name    = "dataflow-scheduler-job"
# schedule = "*/5 * * * *"
# time_zone = "America/New_York"
#
# http_target {
#    http_method = "POST"
#    uri = "${google_cloudfunctions_function.dataflow-function.https_trigger_url}"
#    body = "${base64encode(jsonencode(
#        {
#            runner = "DataflowRunner", 
#            project = "c39-txf-sandbox",
#            temp_location = "gs://c39-txf-sandbox-datalake/tmp", 
#            subnetwork = "https://www.googleapis.com/compute/v1/projects/cloud39-sandbox/regions/us-east1/subnetworks/cloudsql-dataflow-subnet",
#            region =  "us-east1", 
#            requirements_file = "requirements.txt"
#        }
#    ))}" 
# }
# depends_on = [google_project_service.cloud-scheduler-service]
#}

resource "google_cloud_scheduler_job" "job" {
    project = "${var.data_project}"
    region  = "${var.network_region}"
    name     = "dataflow-scheduler-job"
    schedule = "*/10 * * * *"
    time_zone = "America/New_York"

    pubsub_target {
        topic_name = "projects/${var.data_project}/topics/${google_pubsub_topic.dataflow-job-topic.name}"
        # data = "${base64encode(jsonencode(
        #         {
        #             runner = "DataflowRunner", 
        #             project = "c39-txf-sandbox",
        #             temp_location = "gs://c39-txf-sandbox-datalake/tmp", 
        #             subnetwork = "https://www.googleapis.com/compute/v1/projects/cloud39-sandbox/regions/us-east1/subnetworks/cloudsql-dataflow-subnet",
        #             region = "us-east1", 
        #             requirements_file = "requirements.txt"
        #         }
        # ))}"
        # data = "${base64encode(jsonencode([ 
        #                             "--runner", "DataflowRunner",
        #                             "--project", "c39-txf-sandbox",
        #                             "--temp_location", "gs://c39-txf-sandbox-datalake/tmp",
        #                             "--subnetwork", "https://www.googleapis.com/compute/v1/projects/cloud39-sandbox/regions/us-east1/subnetworks/cloudsql-dataflow-subnet", 
        #                             "--region", "us-east1", 
        #                             "--requirements_file", "requirements.txt"
        #                         ]))}"

        data = "${base64encode("--runner DataflowRunner --project c39-txf-sandbox --temp_location gs://c39-txf-sandbox-datalake/tmp --subnetwork https://www.googleapis.com/compute/v1/projects/cloud39-sandbox/regions/us-east1/subnetworks/cloudsql-dataflow-subnet --region us-east1 --requirements_file requirements.txt")}"
    }
    depends_on = [google_project_service.cloud-scheduler-service]
}
