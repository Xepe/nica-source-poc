# infrastructure
host_project = "cloud39-sandbox" # "cloud39-sandbox" #"taxfyle-qa" #
service_project = "c39-txf-sandbox" # "c39-txf-sandbox" # "taxfyle-qa-data" #
network_region = "us-east1" # "us-east1" # "us-central1" #
host_project_sub_network = "cloudsql-dataflow-subnet" # "cloudsql-dataflow-subnet" #"default-kubes-us"
service_project_app_engine_location_id ="us-east1" # "us-east1" #"us-central"
timezone = "America/New_York"

# database connection
db_host = "10.8.240.3" # "10.8.240.3" # "10.248.0.6"
db_port = 5432
db_user = "txf-user" # "txf-user"  # "postgres"
db_password = "Qwerty123" # "Qwerty123" # "PnNZ)58}&k=?jybfpYpi4@TIfB@V{9"

# data destination Big Query dataset
dest_dataset = "main_dwh"

# etl region Data
etl_region = "US"

# ----------------------------------------------
#  data_project = ""
#  main_project = ""
#  cluster_name = ""


# regions = [ 
#     {
#         name = "us",
#         region = "us-central1",
#         sub_network = "",
#         service_project_app_engine_location_id = "", 
#         timezone = "America/New_York",
#         db = {
#               db_host = "10.8.240.3" # "10.8.240.3" # "10.248.0.6"
#               db_port = 5432
#               db_user = "txf-user" # "txf-user"  # "postgres"
#               db_password = "Qwerty123" # "Qwerty123" # "PnNZ)58}&k=?jybfpYpi4@TIfB@V{9"
#         },
#         dest_dataset = "main_dwh"   
#     },
#     {
#         name = "aus",
#         region = "australia-southeast1",
#         sub_network = "" 
#         service_project_app_engine_location_id = "",
#         timezone = "America/New_York",
#         db = {
#               db_host = "10.8.240.3" # "10.8.240.3" # "10.248.0.6"
#               db_port = 5432
#               db_user = "txf-user" # "txf-user"  # "postgres"
#               db_password = "Qwerty123" # "Qwerty123" # "PnNZ)58}&k=?jybfpYpi4@TIfB@V{9"
#         },
#         dest_dataset = "main_dwh"
#     }
# ]
