# Bucket for data
resource "google_storage_bucket" "datalake-bucket" {
  count         = length(var.regions)
  name          = "${var.data_project}-datalake-${lookup(var.regions[count.index], "name")}"
  project       = var.data_project
  location      = lookup(var.regions[count.index], "region")
  force_destroy = true
}

# Bucket for code
resource "google_storage_bucket" "code-bucket" {
  name          = "${var.data_project}-code"
  project       = var.data_project
  location      = "us-central1"
  force_destroy = true
}

# Staging bucket
resource "google_storage_bucket" "staging-bucket" {
    count         = length(var.regions)
    name          = "${var.data_project}-staging-${lookup(var.regions[count.index], "name")}"
    project       = var.data_project    
    location      = lookup(var.regions[count.index], "region")
    force_destroy = true      
}
