data "google_compute_zones" "available" {
  count  = length(var.regions)
  region = lookup(var.regions[count.index], "region")
}

resource "tls_private_key" "ssh-key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "google_compute_instance" "default" {
  count        = length(var.regions)
  name         = "build-pipeline-send-to-dataflow-${lookup(var.regions[count.index], "name")}"
  machine_type = "n1-standard-1"
  zone         = element(data.google_compute_zones.available.*.names[count.index], 0)

  tags = []
  allow_stopping_for_update  = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-minimal-1804-lts"
    }
  }
  
  network_interface {
    network = "default"

    access_config {
      // Ephemeral IP
    }
  }

  metadata = {
    sshKeys = "gcp_user:${tls_private_key.ssh-key.public_key_openssh}"
  }

  service_account {
    email  = "${data.google_project.project.number}-compute@developer.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }

  connection {
    type        = "ssh"
    user        = "gcp_user"
    private_key = tls_private_key.ssh-key.private_key_pem
    host        = self.network_interface.0.access_config.0.nat_ip
  }

  provisioner "file" {
    source      = "./../../code/pipeline_df/main-df.py"
    destination = "/home/gcp_user/main-df.py"
  }

  provisioner "file" {
    source      = "./../../code/pipeline_df/requirements.txt"
    destination = "/home/gcp_user/requirements.txt"
  }

  provisioner "file" {
    source      = "./../../code/pipeline_df/database_table_list.json"
    destination = "/home/gcp_user/database_table_list.json"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update -y",
      "sudo apt-get upgrade -y",
      "sudo apt-get install cron -y",
      "sudo apt update",
      "sudo apt autoremove -y",
      "sudo apt-get install python3-pip -y",
      "sudo pip3 install -r /home/gcp_user/requirements.txt",
      "sudo chmod +x /home/gcp_user/main-df.py",
      "sudo echo '0 */4 * * * sudo /usr/bin/python3 /home/gcp_user/main-df.py --runner DataflowRunner --job_name vm-trigger-pipeline-${lower(lookup(var.regions[count.index], "name"))} --service_account_email ${google_service_account.service-project-service-account-data-pipeline.email} --project ${var.data_project} --temp_location gs://${google_storage_bucket.datalake-bucket.*.name[count.index]}/tmp --staging_location gs://${google_storage_bucket.code-bucket.name}/binaries-${lookup(var.regions[count.index], "name")} --subnetwork https://www.googleapis.com/compute/v1/projects/${var.main_project}/regions/${lookup(var.regions[count.index], "region")}/subnetworks/${var.main_project_sub_network}-${lookup(var.regions[count.index], "name")} --region ${lookup(var.regions[count.index], "dataflow_region")} ${lookup(var.regions[count.index], "dataflow_zone") != "" ? "--zone ${lookup(var.regions[count.index], "dataflow_zone")}" : ""} --requirements_file /home/gcp_user/requirements.txt --db_host ${data.vault_generic_secret.db_creds.data["ip_${lookup(var.regions[count.index], "name")}"]} --db_port ${var.db_port} --db_user ${var.db_user} --db_password \"${replace(data.vault_generic_secret.db_creds.data["password_${lookup(var.regions[count.index], "name")}"], "%", "\\%")}\" --dest_dataset ${var.dest_dataset}_${lookup(var.regions[count.index], "name")} --dest_bucket ${google_storage_bucket.datalake-bucket.*.name[count.index]} --etl_region ${lookup(var.regions[count.index], "name")}' > /home/gcp_user/execute_dataflow",
      "crontab /home/gcp_user/execute_dataflow",
      "sudo systemctl restart cron",
      "sudo crontab -u gcp_user -l"
    ]
  }
}