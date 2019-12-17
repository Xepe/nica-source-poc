# infrastructure
cluster_name             = "staging"
main_project             = "staging-233617"
data_project             = "taxfyle-staging-data"
main_project_sub_network = "default-kubes"

# data destination Big Query dataset
dest_dataset = "data_warehouse"

regions = [
  {
    name                      = "us"
    region                    = "us-central1"
    bigquery_dataset_location = "US"
    cloud_function_region     = "us-central1"
  },
  {
    name                      = "aus"
    region                    = "australia-southeast1"
    bigquery_dataset_location = "australia-southeast1"
    cloud_function_region     = "us-central1"
  }
]

# Dataflow Job notification email
notification_email = "roly.vicaria@taxfyle.com"