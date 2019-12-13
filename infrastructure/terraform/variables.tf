variable "cluster_name" {
  type = string
}

variable "main_project" {
  type = string
}

variable "data_project" {
  type = string
}

variable "main_project_sub_network" {
  type = string
}

variable "dest_dataset" {
  type = string
}
variable "db_port" {
  type    = string
  default = "5432"
}

variable "db_user" {
  type    = string
  default = "postgres"
}

variable "regions" {
  type = list(object({
    name                      = string
    region                    = string
    etl_region                = string
  }))
}

variable "notification_email" {
  type = "string"
}