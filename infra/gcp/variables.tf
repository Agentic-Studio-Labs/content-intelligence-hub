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

variable "db_tier" {
  type        = string
  default     = "db-f1-micro"
  description = "Cloud SQL machine tier (e.g. db-g1-small for dev)."
}

variable "db_public_ipv4_enabled" {
  type        = bool
  default     = true
  description = "Set false when using private IP + VPC connector / Cloud SQL Auth Proxy only."
}

variable "db_ssl_mode" {
  type        = string
  default     = "ENCRYPTED_ONLY"
  description = "Cloud SQL ssl_mode; use ALLOW_UNENCRYPTED_AND_ENCRYPTED only for narrow legacy debugging."
}

variable "db_backup_enabled" {
  type    = bool
  default = false
}

variable "db_deletion_protection" {
  type        = bool
  default     = false
  description = "Enable for production instances."
}

variable "tasks_queue_name" {
  type    = string
  default = "cih-job-queue"
}

variable "tasks_invoker_service_account_email" {
  type        = string
  default     = ""
  description = "Service account email used as Cloud Tasks OIDC identity (must match CIH_CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL)."
}

variable "grant_worker_invoker_to_tasks_sa" {
  type        = bool
  default     = false
  description = "When true and tasks_invoker_service_account_email is set, grant roles/run.invoker on the worker to that SA only."
}

variable "resend_secret_id" {
  type        = string
  default     = ""
  description = "Secret Manager secret id (short name) for the Resend API key. When set, Terraform grants secretAccessor on that secret to the Cloud Run API runtime service account."
}

variable "cloud_run_api_service_account_email" {
  type        = string
  default     = ""
  description = "Runtime service account for cih-api (Cloud Run). Leave empty to use the project default compute SA (PROJECT_NUMBER-compute@developer.gserviceaccount.com)."
}
