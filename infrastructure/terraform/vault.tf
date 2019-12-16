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

# required roles in GCP for vault service account
# BigQuery Data Owner
# Cloud Functions Admin
# Compute Instance Admin (beta)
# Service Account Admin
# Service Account User
# Monitoring Admin
# Pub/Sub Editor
# Project IAM Admin
# Storage Admin
# Storage Object Viewer
