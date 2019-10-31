# infrastructure
host_project = "taxfyle-qa" # "cloud39-sandbox" #"taxfyle-qa" #
service_project = "taxfyle-qa-data" # "c39-txf-sandbox" # "taxfyle-qa-data" #
network_region = "us-central1" # "us-east1" # "us-central1" #
host_project_sub_network = "default-kubes-us" # "cloudsql-dataflow-subnet" #"default-kubes-us"
service_project_app_engine_region ="us-central" # "us-east1" #"us-central"
timezone = "America/New_York"

# database connection
db_host = "10.248.0.6" # "10.8.240.3" # "10.248.0.6"
db_port = 5432
db_user = "postgres" # "txf-user"  # "postgres"
db_password = "replace" # "Qwerty123" # "PnNZ)58}&k=?jybfpYpi4@TIfB@V{9"

# data destination Big Query dataset
dest_dataset = "main_dwh"

etl_region = "us"
environment = "qa"
