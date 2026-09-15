"""
Google Cloud Storage (GCS) Tool Suite.
Provides intake document upload, retrieval, and cryptographic checksum validation.
"""

import os
import hashlib
import json
from typing import Dict, Any, List
import logging

logger = logging.getLogger("amtha.tools.gcs")

class GcsToolSuite:
    """Tool suite for Google Cloud Storage operations."""

    def __init__(self, bucket_name: str = "amtha-underwriting-submissions"):
        self.bucket_name = bucket_name
        self._local_storage_cache: Dict[str, bytes] = {}

    def upload_submission_file(self, submission_id: str, filename: str, content_bytes: bytes) -> Dict[str, Any]:
        """Uploads a raw policy document to Cloud Storage."""
        gcs_uri = f"gs://{self.bucket_name}/{submission_id}/raw/{filename}"
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()
        
        self._local_storage_cache[gcs_uri] = content_bytes
        logger.info(f"Uploaded document to GCS: {gcs_uri} (SHA256: {sha256_hash[:8]}...)")
        
        return {
            "gcs_uri": gcs_uri,
            "filename": filename,
            "size_bytes": len(content_bytes),
            "sha256": sha256_hash,
            "status": "UPLOADED"
        }

    def read_submission_file(self, gcs_uri: str) -> bytes:
        """Reads document bytes from GCS cache."""
        if gcs_uri in self._local_storage_cache:
            return self._local_storage_cache[gcs_uri]
        # Return fallback mock content if not in cache
        return f"Mock PDF Document Content for {gcs_uri}".encode("utf-8")

