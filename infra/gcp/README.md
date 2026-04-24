# GCP Infrastructure

Terraform sketch for the Content Intelligence Hub cloud backend: Cloud Run (API + worker), Cloud SQL, GCS, Cloud Tasks, Secret Manager.

**Local gcloud / Terraform auth:** see [AUTH.md](./AUTH.md) (named `cih` config, ADC, optional SA impersonation).

## Hardening defaults (this module)

| Area | Behavior |
|------|----------|
| **GCS** | Uniform bucket access + **public access prevention enforced** |
| **Cloud SQL** | **`ssl_mode = ENCRYPTED_ONLY`** by default; backups optional; deletion protection off by default (toggle for prod) |
| **Public SQL IP** | **`db_public_ipv4_enabled`** defaults true for simple dev; set **false** and use private networking / connector when ready |
| **Worker** | Optional **`google_cloud_run_v2_service_iam_member`**: grant **`roles/run.invoker`** only to the Cloud Tasks service account (set **`grant_worker_invoker_to_tasks_sa`** and **`tasks_invoker_service_account_email`**) |

The **API** service is still shaped for a **public** Cloud Run URL (magic-link and desktop client). Restrict CORS in the app with **`CIH_CLOUD_CORS_ALLOW_ORIGINS`**.

## Resend (magic-link email)

1. Create a Secret Manager secret and store the Resend API key (Console or `gcloud`).
2. In **`terraform.tfvars`**, set **`resend_secret_id`** to that secret’s **short id** (not the env var name `CIH_CLOUD_RESEND_API_KEY`).
3. Run **`terraform apply`**. This adds **`roles/secretmanager.secretAccessor`** on that secret for the **cih-api** runtime service account (default: **`PROJECT_NUMBER-compute@developer.gserviceaccount.com`**, or override with **`cloud_run_api_service_account_email`** if the service uses a custom SA).
4. In **Cloud Run → cih-api**, mount the secret as environment variable **`CIH_CLOUD_RESEND_API_KEY`** (Console or Terraform once the full service template is managed in code).

## Application guardrails (`cloud/shared/config.py`)

- **`CIH_CLOUD_ENVIRONMENT=production`**: rejects default magic-link/session secrets and rejects **`CIH_CLOUD_SKIP_WORKER_OIDC=true`**.
- **Worker**: verifies **Cloud Tasks OIDC** JWT on `POST /tasks/jobs/{id}` unless **`CIH_CLOUD_SKIP_WORKER_OIDC=true`** (local debugging only).

## Usage

```bash
cd infra/gcp
cp terraform.tfvars.example terraform.tfvars   # edit if needed; tfvars is gitignored
terraform init
terraform plan
```

Set **`grant_worker_invoker_to_tasks_sa=true`** and the tasks SA email after you create that account in IAM (or manage invoker bindings manually in Console).

## Legacy note

V1 files were minimal; re-run **`terraform plan`** before apply — SQL **`ssl_mode`** and bucket **PAP** may update existing resources.
