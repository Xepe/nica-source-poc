resource "tls_private_key" "ssh-key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "google_compute_instance" "default" {
    name         = "build-pipeline-send-to-dataflow"
    machine_type = "n1-standard-1"
    zone         = "${var.network_region}-b"

    tags = []

    boot_disk {
        initialize_params {
        image = "ubuntu-os-cloud/ubuntu-minimal-1804-lts"
        }
    }

    network_interface {
        network = "default"
        #subnetwork = "https://www.googleapis.com/compute/v1/projects/${var.host_project}/regions/${var.network_region}/subnetworks/${var.host_project_sub_network}"

        access_config {
        // Ephemeral IP
        }
    }

    metadata = {    
        sshKeys = "gcp_user:${tls_private_key.ssh-key.public_key_openssh}"
    }

    service_account {
        email = "296783778293-compute@developer.gserviceaccount.com"
        # email  = "${google_service_account.service-project-service-account-data-pipeline.email}"
        scopes = ["cloud-platform"]
    }

    connection {
        type = "ssh"
        user = "gcp_user"
        private_key = "${tls_private_key.ssh-key.private_key_pem}"
        host = "${self.network_interface.0.access_config.0.nat_ip}"   
    }

    provisioner "remote-exec" {
        inline = [
            "sudo apt-get update -y",
            "sudo apt-get upgrade -y",
            "sudo apt-get install cron -y",
            "sudo snap install nano",
            "sudo apt update",
            "sudo apt autoremove -y",
            "sudo apt-get install python3-pip -y",
            "sudo apt-get install htop"
        ]         
    }

    provisioner "file" {
        source      = "./../../code/pipeline_df/main-df.py"
        destination = "/home/gcp_user/main-df.py"   
    }

    provisioner "file" {
        source      = "./../../code/pipeline_df/requirements_vm.txt"
        destination = "/home/gcp_user/requirements.txt"
    }

    provisioner "remote-exec"{
        inline = [
            "sudo pip3 install -r /home/gcp_user/requirements.txt",
            "sudo chmod +x /home/gcp_user/main-df.py",
            # "echo '/usr/bin/python3 /home/gcp_user/main-df.py --runner DataflowRunner --project ${var.service_project} --service_account_email ${google_service_account.service-project-service-account-data-pipeline.email} --temp_location gs://${google_storage_bucket.datalake-bucket.name}/tmp --staging_location gs://${google_storage_bucket.code-bucket.name}/binaries --subnetwork https://www.googleapis.com/compute/v1/projects/${var.host_project}/regions/${var.network_region}/subnetworks/${var.host_project_sub_network} --region ${var.network_region} --requirements_file /home/gcp_user/requirements.txt --db_host ${var.db_host} --db_port ${var.db_port} --db_user ${var.db_user} --db_password \"${var.db_password}\" --dest_dataset ${var.dest_dataset} --dest_bucket ${google_storage_bucket.datalake-bucket.name} --etl_region ${var.etl_region}' > /home/gcp_user/execute_pipeline_${lower(var.etl_region)}.sh",            
            # "sudo chmod +x /home/gcp_user/execute_pipeline_${lower(var.etl_region)}.sh",
            "(crontab -l ; echo '0 */4 * * * /usr/bin/python3 /home/gcp_user/main-df.py --runner DataflowRunner --project ${var.service_project} --temp_location gs://${google_storage_bucket.datalake-bucket.name}/tmp --staging_location gs://${google_storage_bucket.code-bucket.name}/binaries --subnetwork https://www.googleapis.com/compute/v1/projects/${var.host_project}/regions/${var.network_region}/subnetworks/${var.host_project_sub_network} --region ${var.network_region} --requirements_file /home/gcp_user/requirements.txt --db_host ${var.db_host} --db_port ${var.db_port} --db_user ${var.db_user} --db_password \"${var.db_password}\" --dest_dataset ${var.dest_dataset} --dest_bucket ${google_storage_bucket.datalake-bucket.name} --etl_region ${var.etl_region}') | sort - | uniq - | crontab -",
            # "(crontab -l ; echo '0 */4 * * * /bin/sh /home/gcp_user/execute_pipeline_${lower(var.etl_region)}.sh') | sort - | uniq - | crontab -",
            "sudo systemctl restart cron",
            "sudo crontab -u gcp_user -l"            
        ]
    }
}



