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
# 3. Public access — required so requests can reach the container at all.
#    Firebase Auth (anonymous or otherwise) does NOT replace this binding:
#    Firebase-issued tokens are not GCP IAM principals, so Cloud Run would
#    reject every request at this layer before your app-level Firebase
#    token check ever runs. Access control for Firebase users happens
#    INSIDE the app (see auth.validate_key), not here.
#
#    Only remove/replace this block if you switch to IAP, which integrates
#    with Cloud Run's IAM layer directly (requires a load balancer in front
#    of this service — see the Cloud Armor/rate-limiting discussion).
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = google_cloud_run_v2_service.app.project
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ---------------------------------------------------------------------------
# 4. Required for firebase_admin.auth.verify_id_token() calls in utils.py
#    Grants the runtime SA Firebase Auth admin access, used by
#    firebase_admin.auth.verify_id_token() in utils.py to validate guest
#    session tokens on each request.
#    NOTE: verify_id_token() validates tokens against Firebase's public keys
#    and may not actually require this role — it's broader than strictly
#    needed (firebaseauth.admin also grants user-management permissions).
#    Test removing this binding; keep only if verification fails without it.
# ---------------------------------------------------------------------------
resource "google_project_iam_member" "app_runtime_firebase" {
  project = "genai-app-startupval-prototype"
  role    = "roles/firebaseauth.admin"
  member  = "serviceAccount:${google_service_account.app_runtime.email}"
}

output "service_url" {
  value = google_cloud_run_v2_service.app.uri
}
