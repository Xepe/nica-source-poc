# Service account in service project
resource "google_service_account" "service-project-service-account-data-pipeline" {
    project = "${var.service_project}"
    account_id   = "service-account-data-pipeline"
    display_name = "Dataflow Service Account for execute Taxfyle data pipeline"
}

# Grant access in service project (access network, execute dataflow pipeline, save data to big query, save data to storage)
# Grant access to shared VPC
resource "google_project_iam_member" "service-project-service-account-data-pipeline-shared-vpc" {
    project = "${var.service_project}"
    role    = "roles/compute.networkUser"
    member = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
    depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

#bind subnet to dataflow and serviceAccount
data "google_project" "project" {}
    output "project_number" {
    value = "${data.google_project.project.number}"
} 

resource "google_compute_subnetwork_iam_binding" "subnet" {
    project = "${var.host_project}"
    region = "${var.network_region}"
    subnetwork = "${var.host_project_sub_network}"
    role       = "roles/compute.networkUser"

    members = [
        "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}",
        "serviceAccount:service-${data.google_project.project.number}@dataflow-service-producer-prod.iam.gserviceaccount.com"
    ]
}

# Grant access to execute dataflow worker in the service project
resource "google_project_iam_member" "service-project-service-account-data-pipeline-df-worker" {
    project = "${var.service_project}"
    role    = "roles/dataflow.worker"
    member = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
    depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access to save data to bukects in the service project 
resource "google_project_iam_member" "service-project-service-account-data-pipeline-admin-buckets" {
    project = "${var.service_project}"
    role    = "roles/storage.objectAdmin" 
    member = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
    depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access to save data to big query in the service project
resource "google_project_iam_member" "service-project-service-account-data-pipeline-admin-bq" {
    project = "${var.service_project}"
    role    = "roles/bigquery.admin"
    member = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
    depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access in host project (access network, access SQL intance)
# Grant access to shared VPC
resource "google_project_iam_member" "host-project-service-account-data-pipeline-shared-vpc" {
    project = "${var.host_project}"
    role    = "roles/compute.networkUser"
    member = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
    depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access to host project cloud sql
resource "google_project_iam_member" "host-project-service-account-data-pipeline-sql-client" {
    project = "${var.host_project}"
    role    = "roles/cloudsql.client"
    member = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
    depends_on = [google_service_account.service-project-service-account-data-pipeline]
}