provider "google" {
    region  = "us-west1"
    project = "${var.service_project}"

  # access_token = "${data.vault_generic_secret.gcp_auth_token.data["token"]}"
}