terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_project" "project" {
  project_id = var.project_id
}

locals {
  # Cloud Run default runtime SA when template.service_account is unset.
  cloud_run_api_sa = (
    var.cloud_run_api_service_account_email != ""
    ? var.cloud_run_api_service_account_email
    : "${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  )
}

resource "google_storage_bucket" "artifacts" {
  name                        = var.artifact_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
}

resource "google_sql_database_instance" "cloud_sql" {
  name             = var.db_instance_name
  region           = var.region
  database_version = "POSTGRES_15"

  deletion_protection = var.db_deletion_protection

  settings {
    tier = var.db_tier

    ip_configuration {
      ipv4_enabled = var.db_public_ipv4_enabled
      ssl_mode     = var.db_ssl_mode
    }

    backup_configuration {
      enabled = var.db_backup_enabled
    }
  }
}

resource "google_cloud_tasks_queue" "jobs" {
  name     = var.tasks_queue_name
  location = var.region
}

resource "google_secret_manager_secret" "anthropic" {
  secret_id = "anthropic-primary"

  replication {
    auto {}
  }
}

# Resend API key: create the secret and secret versions outside Terraform, then set
# resend_secret_id to that secret's id. Grants the API Cloud Run runtime SA read access.
data "google_secret_manager_secret" "resend" {
  count     = var.resend_secret_id != "" ? 1 : 0
  secret_id = var.resend_secret_id
}

resource "google_secret_manager_secret_iam_member" "api_resend_accessor" {
  count     = var.resend_secret_id != "" ? 1 : 0
  secret_id = data.google_secret_manager_secret.resend[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloud_run_api_sa}"
}

resource "google_cloud_run_v2_service" "api" {
  name     = "cih-api"
  location = var.region

  template {
    containers {
      image = "us-docker.pkg.dev/${var.project_id}/cih/cih-api:latest"
    }
  }
}

resource "google_cloud_run_v2_service" "worker" {
  name     = "cih-worker"
  location = var.region

  template {
    containers {
      image = "us-docker.pkg.dev/${var.project_id}/cih/cih-worker:latest"
    }
  }
}

# Grant the Cloud Tasks OIDC service account permission to call the worker only
# (remove any roles/run.invoker binding for allUsers on the worker in Cloud Console if present).
resource "google_cloud_run_v2_service_iam_member" "worker_invoker_tasks_sa" {
  count = var.grant_worker_invoker_to_tasks_sa ? 1 : 0

  project  = var.project_id
  location = google_cloud_run_v2_service.worker.location
  name     = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.tasks_invoker_service_account_email}"
}
