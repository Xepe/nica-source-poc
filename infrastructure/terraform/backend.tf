terraform {
  backend "gcs" {
    prefix      = ""
    credentials = "gcs_backend_creds"

    # The following properties are being passed in via Makefile
    # Refer to Terraform partial configuration docs
    # bucket  = "${var.cluster_name}-tf-backend"
  }
}
