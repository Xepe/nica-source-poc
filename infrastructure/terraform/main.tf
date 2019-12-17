provider "google" {
  region  = "us-central1"
  project = var.data_project

  access_token = data.vault_generic_secret.gcp_auth_token.data["token"]
}
