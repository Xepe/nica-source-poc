# Service account in service project
resource "google_service_account" "service-project-service-account-data-pipeline" {
  project      = var.data_project
  account_id   = "service-account-data-pipeline"
  display_name = "Dataflow Service Account for execute Taxfyle data pipeline"
}

# Grant access in service project (access network, execute dataflow pipeline, save data to big query, save data to storage)
# Grant access to shared VPC
resource "google_project_iam_member" "service-project-service-account-data-pipeline-shared-vpc" {
  project    = var.data_project
  role       = "roles/compute.networkUser"
  member     = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
  depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

#bind subnet to dataflow and serviceAccount
data "google_project" "project" {}

output "project_number" {
  value = data.google_project.project.number
}

resource "google_compute_subnetwork_iam_binding" "subnet" {
  count      = length(var.regions)
  project    = var.main_project
  region     = lookup(var.regions[count.index], "region")
  subnetwork = "${var.main_project_sub_network}-${lookup(var.regions[count.index], "name")}"
  role       = "roles/compute.networkUser"

  members = [
    "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}",
    "serviceAccount:service-${data.google_project.project.number}@dataflow-service-producer-prod.iam.gserviceaccount.com",
  ]
}

# Grant access to execute dataflow worker in the service project
resource "google_project_iam_member" "service-project-service-account-data-pipeline-df-worker" {
  project    = var.data_project
  role       = "roles/dataflow.worker"
  member     = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
  depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access to save data to bukects in the service project 
resource "google_project_iam_member" "service-project-service-account-data-pipeline-admin-buckets" {
  project    = var.data_project
  role       = "roles/storage.admin"
  member     = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
  depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access to save data to big query in the service project
resource "google_project_iam_member" "service-project-service-account-data-pipeline-admin-bq" {
  project    = var.data_project
  role       = "roles/bigquery.admin"
  member     = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
  depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access to publish message to a pubsub
resource "google_project_iam_member" "service-project-service-account-data-pipeline-publish-pubsub" {
  project    = var.data_project
  role       = "roles/pubsub.publisher"
  member     = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
  depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access to invoke Cloud functions
resource "google_project_iam_member" "service-project-service-account-data-pipeline-invoke-cloud-function" {
  project    = var.data_project
  role       = "roles/cloudfunctions.invoker"
  member     = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
  depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access in host project (access network, access SQL intance)
# Grant access to shared VPC
resource "google_project_iam_member" "host-project-service-account-data-pipeline-shared-vpc" {
  project    = var.main_project
  role       = "roles/compute.networkUser"
  member     = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
  depends_on = [google_service_account.service-project-service-account-data-pipeline]
}

# Grant access to host project cloud sql
resource "google_project_iam_member" "host-project-service-account-data-pipeline-sql-client" {
  project    = var.main_project
  role       = "roles/cloudsql.client"
  member     = "serviceAccount:${google_service_account.service-project-service-account-data-pipeline.email}"
  depends_on = [google_service_account.service-project-service-account-data-pipeline]
}
