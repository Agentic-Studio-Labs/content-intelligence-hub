variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "artifact_bucket_name" {
  type    = string
  default = "cih-artifacts-dev"
}

variable "db_instance_name" {
  type    = string
  default = "cih-cloud-sql"
}
