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

resource "google_storage_bucket" "artifacts" {
  name                        = var.artifact_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
}

resource "google_sql_database_instance" "cloud_sql" {
  name             = var.db_instance_name
  region           = var.region
  database_version = "POSTGRES_15"

  settings {
    tier = "db-f1-micro"
  }
}

resource "google_cloud_tasks_queue" "jobs" {
  name     = "cih-job-queue"
  location = var.region
}

resource "google_secret_manager_secret" "anthropic" {
  secret_id = "anthropic-primary"

  replication {
    auto {}
  }
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
