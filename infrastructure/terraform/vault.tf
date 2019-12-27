provider "vault" {
  /*
   * The config for this provider is pulled
   * from the environment. Once you setup
   * and login to vault cli locally, this
   * provider will use same config.
   */
}

data "vault_generic_secret" "gcp_auth_token" {
  path = "gcp/token/tf-${var.cluster_name}-roleset"
}

data "vault_generic_secret" "db_creds" {
  path = "${var.cluster_name}/db_creds"
}

# required roles in GCP for vault service account in data_project
# BigQuery Data Owner               "roles/bigquery.dataOwner"
# Cloud Functions Admin             "roles/cloudfunctions.admin"
# Compute Instance Admin (beta)     "roles/compute.instanceAdmin"
# Service Account Admin             "roles/iam.serviceAccountAdmin"
# Service Account User              "roles/iam.serviceAccountUser"              
# Monitoring Admin                  "roles/monitoring.admin"                    
# Pub/Sub Editor                    "roles/pubsub.editor"                       
# Project IAM Admin                 "roles/resourcemanager.projectIamAdmin"
# Storage Admin                     "roles/storage.admin"
# Storage Object Viewer             "roles/storage.objectViewer"
