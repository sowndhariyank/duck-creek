"""
Configuration settings for Amtha Underwriting Multi-Agent Platform.
Adheres strictly to Gemini Enterprise on Vertex AI and Google Gen AI SDK standards.
"""

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    # Google Cloud Project & Location
    gcp_project_id: str = os.getenv("GOOGLE_CLOUD_PROJECT", "arsanjani-genai")
    gcp_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    use_vertex_ai: bool = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
    
    # PaaS Service Mock / Trial Flags
    use_mock_apigee: bool = os.getenv("USE_MOCK_APIGEE", "true").lower() == "true"
    use_mock_looker: bool = os.getenv("USE_MOCK_LOOKER", "true").lower() == "true"
    use_mock_docai: bool = os.getenv("USE_MOCK_DOCAI", "true").lower() == "true"
    use_mock_bigquery: bool = os.getenv("USE_MOCK_BIGQUERY", "true").lower() == "true"

    # GCS Bucket Settings
    gcs_submissions_bucket: str = os.getenv("GCS_SUBMISSIONS_BUCKET", "amtha-underwriting-submissions")

    # Actuarial Rule Set Version
    active_rating_rule_version: str = os.getenv("ACTIVE_RATING_RULE_VERSION", "v2026.3")

    # Server Settings
    server_host: str = os.getenv("HOST", "0.0.0.0")
    server_port: int = int(os.getenv("PORT", "8080"))

config = AppConfig()

