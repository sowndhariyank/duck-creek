terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.20"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable All 9 Required Google Cloud APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "storage.googleapis.com",              # 1. Cloud Storage API
    "documentai.googleapis.com",           # 2. Document AI API
    "bigquery.googleapis.com",             # 3. BigQuery API
    "apigee.googleapis.com",               # 4. Apigee API
    "looker.googleapis.com",               # 5. Looker API
    "networkservices.googleapis.com",      # 6. Agent Gateway API (Envoy)
    "iamcredentials.googleapis.com",       # 7. Agent Identity API (SPIFFE)
    "container.googleapis.com",            # 8. GKE API
    "run.googleapis.com",                  # 9. Cloud Run API
    "aiplatform.googleapis.com"            # Vertex AI for Gemini Enterprise
  ])
  service            = each.key
  disable_on_destroy = false
}

# 1. Google Cloud Storage (Submission Intake Repository)
resource "google_storage_bucket" "submissions_bucket" {
  name                        = "${var.project_id}-amtha-submissions"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
  depends_on = [google_project_service.required_apis]
}

# 2. Document AI Processor
resource "google_document_ai_processor" "insurance_form_parser" {
  location     = "us"
  display_name = "amtha-insurance-form-parser"
  type         = "FORM_PARSER_PROCESSOR"
  depends_on   = [google_project_service.required_apis]
}

# 3. BigQuery Underwriting Dataset & Event Ledger
resource "google_bigquery_dataset" "underwriting_dw" {
  dataset_id                  = "amtha_underwriting_dw"
  location                    = var.region
  description                 = "Durable Quote Lifecycle Ledger and Claims Vector Store"
  depends_on                  = [google_project_service.required_apis]
}

resource "google_bigquery_table" "quote_lifecycle_events" {
  dataset_id = google_bigquery_dataset.underwriting_dw.dataset_id
  table_id   = "quote_lifecycle_events"

  time_partitioning {
    type = "DAY"
  }

  schema = jsonencode([
    {"name": "event_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "quote_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "submission_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "from_state", "type": "STRING", "mode": "REQUIRED"},
    {"name": "to_state", "type": "STRING", "mode": "REQUIRED"},
    {"name": "event_name", "type": "STRING", "mode": "REQUIRED"},
    {"name": "actor_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "metadata_json", "type": "STRING", "mode": "NULLABLE"},
    {"name": "timestamp_utc", "type": "FLOAT64", "mode": "REQUIRED"}
  ])
}

# 4. Cloud Run: Multi-Agent Reactive Orchestration Service
resource "google_cloud_run_v2_service" "agent_orchestrator" {
  name     = "amtha-agent-orchestrator"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "gcr.io/${var.project_id}/amtha-orchestrator:latest"
      
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "true"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# 5. GKE Autopilot Cluster (High-Throughput Batch Processing & Sidecars)
resource "google_container_cluster" "compute_cluster" {
  name             = "amtha-compute-cluster"
  location         = var.region
  enable_autopilot = true
  depends_on       = [google_project_service.required_apis]
}

