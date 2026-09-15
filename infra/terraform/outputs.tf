output "cloud_run_service_url" {
  description = "The URL of the deployed Cloud Run Multi-Agent Orchestrator"
  value       = google_cloud_run_v2_service.agent_orchestrator.uri
}

output "submissions_bucket_name" {
  description = "Name of the intake GCS bucket"
  value       = google_storage_bucket.submissions_bucket.name
}

output "bigquery_dataset_id" {
  description = "Dataset ID for the underwriting ledger"
  value       = google_bigquery_dataset.underwriting_dw.dataset_id
}

output "gke_cluster_name" {
  description = "GKE Compute Cluster Name"
  value       = google_container_cluster.compute_cluster.name
}

