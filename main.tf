terraform {
  backend "gcs" {
    bucket = "genai-app-startupval-prototype-terraform-state"
    prefix = "terraform/state"
  }
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "genai-app-startupval-prototype"
  region  = "us-central1"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

# ---------------------------------------------------------------------------
# 1. Dedicated least-privilege runtime service account for the Cloud Run app
#    (do NOT let the service run as the default compute SA)
# ---------------------------------------------------------------------------
resource "google_service_account" "app_runtime" {
  account_id   = "genai-app-runtime"
  display_name = "GenAI Startup Valuation App Runtime SA"
}

# Grant only what the app actually needs at runtime.
# Example: if calling Vertex AI / Gemini
resource "google_project_iam_member" "app_runtime_vertex_ai" {
  project = "genai-app-startupval-prototype"
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.app_runtime.email}"
}

# ---------------------------------------------------------------------------
# 2. Cloud Run service definition — the "shape" Terraform owns.
#    Cloud Build will only ever update the `image` field on top of this.
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "app" {
  name     = "genai-app-startupvaluationsummary-p-1-17852309392"
  location = "us-central1"
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.app_runtime.email

    scaling {
      max_instance_count = 10
      min_instance_count = 0
    }

    timeout = "60s"

    containers {
      image = "us-central1-docker.pkg.dev/genai-app-startupval-prototype/cloud-run-source-deploy/genai-app-startupvaluationsummary-prototype/genai-app-startupvaluationsummary-p-1-17852309392:${var.image_tag}"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }
}

# ---------------------------------------------------------------------------
# 3. Public access — explicit, conscious decision (matches current public app)
#    Change to remove this block once you add an auth layer (IAP/Firebase Auth).
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = google_cloud_run_v2_service.app.project
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_v2_service.app.uri
}
