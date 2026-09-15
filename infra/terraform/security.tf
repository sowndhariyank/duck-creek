# Agent Identity (SPIFFE) & Workload Identity Federation
resource "google_service_account" "agent_orchestrator_sa" {
  account_id   = "amtha-agent-orchestrator-sa"
  display_name = "Amtha Underwriting Orchestrator Service Account"
}

# Grant Least-Privilege IAM Roles
resource "google_project_iam_member" "docai_user" {
  project = var.project_id
  role    = "roles/documentai.viewer"
  member  = "serviceAccount:${google_service_account.agent_orchestrator_sa.email}"
}

resource "google_project_iam_member" "gcs_user" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.agent_orchestrator_sa.email}"
}

resource "google_project_iam_member" "bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.agent_orchestrator_sa.email}"
}

resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_orchestrator_sa.email}"
}

