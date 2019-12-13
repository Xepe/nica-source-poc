# infrastructure
cluster_name             = "qa"
main_project             = "taxfyle-qa"
data_project             = "taxfyle-qa-data"
main_project_sub_network = "default-kubes"

# data destination Big Query dataset
dest_dataset = "data_warehouse"

regions = [
  {
    name                      = "us"
    region                    = "us-central1"
    etl_region                = "us"
  }
]

# Dataflow Job notification email
notification_email = "roly.vicaria@taxfyle.com"