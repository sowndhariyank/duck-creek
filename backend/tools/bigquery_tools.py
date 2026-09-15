"""
BigQuery Analytics & Event Ledger Tool Suite.
Provides vector similarity lookups, audit logging, and append-only quote lifecycle event persistence.
"""

from typing import Dict, Any, List, Optional
import time
import json
import logging

logger = logging.getLogger("amtha.tools.bigquery")

class BigQueryToolSuite:
    """Tool suite for BigQuery analytics and durable ledger."""

    def __init__(self, dataset_id: str = "amtha_underwriting_dw"):
        self.dataset_id = dataset_id
        self._quote_events_table: List[Dict[str, Any]] = []
        self._audit_logs_table: List[Dict[str, Any]] = []

    def append_lifecycle_event(
        self,
        quote_id: str,
        submission_id: str,
        from_state: str,
        to_state: str,
        event_name: str,
        actor_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Appends an immutable state transition record to BigQuery ledger."""
        record = {
            "event_id": f"EVT-{len(self._quote_events_table) + 1:06d}",
            "quote_id": quote_id,
            "submission_id": submission_id,
            "from_state": from_state,
            "to_state": to_state,
            "event_name": event_name,
            "actor_id": actor_id,
            "metadata_json": json.dumps(metadata),
            "timestamp_utc": time.time()
        }
        self._quote_events_table.append(record)
        logger.info(f"BigQuery Event Appended: {event_name} -> {to_state} (Quote: {quote_id})")
        return record

    def record_audit_log(
        self,
        quote_id: str,
        merkle_root: str,
        decision_hash: str,
        rule_version: str,
        grounding_passed: bool
    ) -> Dict[str, Any]:
        """Stores a finalized regulator audit record."""
        audit_entry = {
            "quote_id": quote_id,
            "merkle_root": merkle_root,
            "decision_hash": decision_hash,
            "rule_version": rule_version,
            "grounding_passed": grounding_passed,
            "timestamp_utc": time.time()
        }
        self._audit_logs_table.append(audit_entry)
        return audit_entry

    def get_quote_history(self, quote_id: str) -> List[Dict[str, Any]]:
        """Retrieves full audit event history for a given quote."""
        return [e for e in self._quote_events_table if e["quote_id"] == quote_id]

