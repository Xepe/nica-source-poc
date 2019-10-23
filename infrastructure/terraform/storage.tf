# This is the Google Cloud Storage where the data lake will be created
resource "google_storage_bucket" "datalake-bucket" {
    name    = "${var.data_project}-datalake"
    project = "${var.data_project}"
}

# Bucket for terraform etl-tfstate
resource "google_storage_bucket" "etl-tfstate-bucket" {
    name    = "${var.data_project}-qa-data-etl-tfstate"
    project = "${var.data_project}"
}

# Bucket for code
resource "google_storage_bucket" "code-bucket" {
    name    = "${var.data_project}-code"
    project = "${var.data_project}"
}

#copy code files as zip file
data "archive_file" "code" {
  type        = "zip"
  output_path = "./../../code.zip"
  depends_on = [google_storage_bucket.code-bucket]

  source {
    content  = ".txt"
    filename = "./../../requirements.txt"
  }

  source {
    content  = ".py"
    filename = "./../../main.py"
  }  
}
