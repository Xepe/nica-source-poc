# Bucket for data
resource "google_storage_bucket" "datalake-bucket" {
    name    = "${var.data_project}-datalake"
    project = "${var.data_project}"
    force_destroy = true
}

# Bucket for terraform etl-tfstate
resource "google_storage_bucket" "etl-tfstate-bucket" {
    name    = "${var.data_project}-qa-data-etl-tfstate"
    project = "${var.data_project}"
    force_destroy = true
}

# Bucket for Python code
resource "google_storage_bucket" "code-bucket" {
    name    = "${var.data_project}-code"
    project = "${var.data_project}"
    force_destroy = true
}

# Zip Python Code folder
data "archive_file" "code" {
  type        = "zip"
  source_dir = "./../../code/"
  output_path = ".${replace(path.module, path.root, "")}/code/code.zip"  
}

# Provisioning code to bucket
resource "google_storage_bucket_object" "application-zip" {
  name   = "code.zip"
  source = ".${replace(path.module, path.root, "")}/code/code.zip"
  bucket = "${google_storage_bucket.code-bucket.name}"
  depends_on = [google_storage_bucket.code-bucket]
}

