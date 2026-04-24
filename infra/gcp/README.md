# GCP Infrastructure Skeleton

This directory holds the first-pass infrastructure definition for the cloud migration.

V1 targets:
- Cloud Run API service
- Cloud Run worker service
- Cloud SQL instance
- Cloud Storage bucket for uploads and artifacts
- Secret Manager entries for provider credentials
- Cloud Tasks queue for async job dispatch

The Terraform files here are intentionally minimal and establish the core resource shape
without locking the project into a full production rollout yet.
