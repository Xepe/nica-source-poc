# ------------------------------------- pubsub cloud functions ------------------------------------------------------

# post_dataflow_processing
locals {
  bq_post_dataflow_processing_gcs_filename = "bq_post_dataflow_processing_function_${substr(lower(replace(base64encode(data.archive_file.bq-post-dataflow-processing.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python bq_post_dataflow_processing folder
data "archive_file" "bq-post-dataflow-processing" {
  type        = "zip"
  source_dir  = "./../../code/pubsub/bq_post_dataflow_processing"
  output_path = ".${replace(path.module, path.root, "")}/code/bq_post_dataflow_processing.zip"
}

# Provisioning bq_post_dataflow_processing to bucket
resource "google_storage_bucket_object" "bq-post-dataflow-processing-zip" {
  name       = local.bq_post_dataflow_processing_gcs_filename
  source     = ".${replace(path.module, path.root, "")}/code/bq_post_dataflow_processing.zip"
  bucket     = google_storage_bucket.code-bucket.name
  depends_on = [google_storage_bucket.code-bucket]
}


# notify_schema_error_importing_json_file
locals {
  bq_notify_schema_error_importing_json_file_filename = "bq_notify_schema_error_importing_json_file_function_${substr(lower(replace(base64encode(data.archive_file.bq-notify-schema-error-importing-json-file.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python bq_notify_schema_error_importing_json_file folder
data "archive_file" "bq-notify-schema-error-importing-json-file" {
  type        = "zip"
  source_dir  = "./../../code/pubsub/bq_notify_schema_error_importing_json_file"
  output_path = ".${replace(path.module, path.root, "")}/code/bq_notify_schema_error_importing_json_file.zip"
}

# Provisioning notify_error_importing_json_file to bucket
resource "google_storage_bucket_object" "bq-notify-schema-error-importing-json-file-zip" {
  name       = local.bq_notify_schema_error_importing_json_file_filename
  source     = ".${replace(path.module, path.root, "")}/code/bq_notify_schema_error_importing_json_file.zip"
  bucket     = google_storage_bucket.code-bucket.name
  depends_on = [google_storage_bucket.code-bucket]
}

# notify_data_error_importing_json_file
locals {
  bq_notify_data_error_importing_json_file_filename = "bq_notify_data_error_importing_json_file_function_${substr(lower(replace(base64encode(data.archive_file.bq-notify-data-error-importing-json-file.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python bq_notify_data_error_importing_json_file folder
data "archive_file" "bq-notify-data-error-importing-json-file" {
  type        = "zip"
  source_dir  = "./../../code/pubsub/bq_notify_data_error_importing_json_file"
  output_path = ".${replace(path.module, path.root, "")}/code/bq_notify_data_error_importing_json_file.zip"
}

# Provisioning notify_error_importing_json_file to bucket
resource "google_storage_bucket_object" "bq-notify-data-error-importing-json-file-zip" {
  name       = local.bq_notify_data_error_importing_json_file_filename
  source     = ".${replace(path.module, path.root, "")}/code/bq_notify_data_error_importing_json_file.zip"
  bucket     = google_storage_bucket.code-bucket.name
  depends_on = [google_storage_bucket.code-bucket]
}

# bq_create_views_and_cleanup
locals {
  bq_create_views_and_cleanup_filename = "bq_create_views_and_cleanup_function_${substr(lower(replace(base64encode(data.archive_file.bq-create-views-and-cleanup.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python bq_create_views_and_cleanup folder
data "archive_file" "bq-create-views-and-cleanup" {
  type        = "zip"
  source_dir  = "./../../code/pubsub/bq_create_views_and_cleanup"
  output_path = ".${replace(path.module, path.root, "")}/code/bq_create_views_and_cleanup.zip"
}

# Provisioning bq_create_views_and_cleanup to bucket
resource "google_storage_bucket_object" "bq-create-views-and-cleanup-zip" {
  name       = local.bq_create_views_and_cleanup_filename
  source     = ".${replace(path.module, path.root, "")}/code/bq_create_views_and_cleanup.zip"
  bucket     = google_storage_bucket.code-bucket.name
  depends_on = [google_storage_bucket.code-bucket]
}

# df_cleanup
locals {
  df_cleanup_filename = "df_cleanup_function_${substr(lower(replace(base64encode(data.archive_file.df-cleanup.output_md5), "=", "")), 0, 15)}.zip"
}

# Zip Python df_cleanup folder
data "archive_file" "df-cleanup" {
  type        = "zip"
  source_dir  = "./../../code/pubsub/df_cleanup"
  output_path = ".${replace(path.module, path.root, "")}/code/df_cleanup.zip"
}

# Provisioning df_cleanup to bucket
resource "google_storage_bucket_object" "df-cleanup-zip" {
  name       = local.df_cleanup_filename
  source     = ".${replace(path.module, path.root, "")}/code/df_cleanup.zip"
  bucket     = google_storage_bucket.code-bucket.name
  depends_on = [google_storage_bucket.code-bucket]
}


# ----------------------------------------pipeline function---------------------------------------------------- 

# main_df.py, requirements.txt, database_table_list.json files
resource "null_resource" "reprovisioning-pipeline-code" {
  count = length(var.regions)
  triggers = {
    main_df_sha1      = "${sha1(file("./../../code/pipeline_df/main-df.py"))}",
    requirements_sha1 = "${sha1(file("./../../code/pipeline_df/requirements.txt"))}",
    table_list_sha1   = "${sha1(file("./../../code/pipeline_df/database_table_list.json"))}"
  }

  connection {
    type        = "ssh"
    user        = "gcp_user"
    private_key = tls_private_key.ssh-key.private_key_pem
    host        = google_compute_instance.default[count.index].network_interface.0.access_config.0.nat_ip
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
      "sudo pip3 install -r /home/gcp_user/requirements.txt",
      "sudo chmod +x /home/gcp_user/main-df.py"
    ]
  } 

  depends_on = [tls_private_key.ssh-key, google_compute_instance.default]
}


# ----------------------------------------cron configuration---------------------------------------------------- 

resource "null_resource" "reprovisioning-cron-template" {
  count = length(var.regions)
  triggers = {
    cron_template_sha1   = "${sha1(data.template_file.cron_template[count.index].rendered)}",
    cron_frequecy_sha1   = "${sha1(local.cron_command)}"
  }

  connection {
    type        = "ssh"
    user        = "gcp_user"
    private_key = tls_private_key.ssh-key.private_key_pem
    host        = google_compute_instance.default[count.index].network_interface.0.access_config.0.nat_ip
  }

  provisioner "file" {
    content     = data.template_file.cron_template[count.index].rendered
    destination = "/home/gcp_user/execute_pipeline.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo chmod +x /home/gcp_user/execute_pipeline.sh", 
      local.cron_command,
      "sudo systemctl restart cron",
      "sudo crontab -u gcp_user -l"
    ]
  }  

  depends_on = [tls_private_key.ssh-key, google_compute_instance.default]
}