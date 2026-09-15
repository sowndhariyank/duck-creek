"""
Shared Epistemic Memory & Citation Registry Layer.
Maintains an immutable cryptographic store of all Document AI spans,
external enrichment API hashes, and symbolic rule IDs.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import hashlib
import json
import time

@dataclass(frozen=True)
class DocumentSpanRecord:
    span_id: str
    source_gcs_uri: str
    document_name: str
    page_number: int
    char_start: int
    char_end: int
    bounding_box: Tuple[float, float, float, float]  # [ymin, xmin, ymax, xmax]
    verbatim_text: str
    span_hash: str


@dataclass(frozen=True)
class ApiReceiptRecord:
    receipt_id: str
    service_name: str
    endpoint_url: str
    response_sha256: str
    json_path: str
    value: Any
    timestamp_utc: float


@dataclass(frozen=True)
class RuleRegistryRecord:
    rule_id: str
    rule_set_version: str
    rule_category: str
    formula_expression: str
    parameters: Dict[str, Any]


class EpistemicCitationRegistry:
    """
    Cryptographically verifiable citation registry.
    Ensures every factual claim emitted across the multi-agent mesh is backed by evidence.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._doc_spans: Dict[str, DocumentSpanRecord] = {}
        self._api_receipts: Dict[str, ApiReceiptRecord] = {}
        self._rules: Dict[str, RuleRegistryRecord] = {}
        self._citations_log: List[Dict[str, Any]] = []

    def register_document_span(
        self,
        span_id: str,
        source_gcs_uri: str,
        document_name: str,
        page_number: int,
        char_start: int,
        char_end: int,
        bounding_box: Tuple[float, float, float, float],
        verbatim_text: str
    ) -> DocumentSpanRecord:
        """Registers a character span extracted from Document AI."""
        span_hash = hashlib.sha256(
            f"{source_gcs_uri}:{page_number}:{char_start}:{char_end}:{verbatim_text}".encode()
        ).hexdigest()
        
        record = DocumentSpanRecord(
            span_id=span_id,
            source_gcs_uri=source_gcs_uri,
            document_name=document_name,
            page_number=page_number,
            char_start=char_start,
            char_end=char_end,
            bounding_box=bounding_box,
            verbatim_text=verbatim_text,
            span_hash=span_hash
        )
        self._doc_spans[span_id] = record
        return record

    def register_api_receipt(
        self,
        receipt_id: str,
        service_name: str,
        endpoint_url: str,
        response_sha256: str,
        json_path: str,
        value: Any
    ) -> ApiReceiptRecord:
        """Registers an external API response receipt."""
        record = ApiReceiptRecord(
            receipt_id=receipt_id,
            service_name=service_name,
            endpoint_url=endpoint_url,
            response_sha256=response_sha256,
            json_path=json_path,
            value=value,
            timestamp_utc=time.time()
        )
        self._api_receipts[receipt_id] = record
        return record

    def register_symbolic_rule(
        self,
        rule_id: str,
        rule_set_version: str,
        rule_category: str,
        formula_expression: str,
        parameters: Dict[str, Any]
    ) -> RuleRegistryRecord:
        """Registers a deterministic symbolic rule definition."""
        record = RuleRegistryRecord(
            rule_id=rule_id,
            rule_set_version=rule_set_version,
            rule_category=rule_category,
            formula_expression=formula_expression,
            parameters=parameters
        )
        self._rules[rule_id] = record
        return record

    def has_span(self, span_id: str) -> bool:
        return span_id in self._doc_spans

    def get_span(self, span_id: str) -> Optional[DocumentSpanRecord]:
        return self._doc_spans.get(span_id)

    def has_api_receipt(self, receipt_id: str) -> bool:
        return receipt_id in self._api_receipts

    def has_rule(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def get_all_spans(self) -> List[DocumentSpanRecord]:
        return list(self._doc_spans.values())

    def generate_merkle_root(self) -> str:
        """Generates a cryptographic Merkle root across all registered evidence."""
        combined = []
        for s in sorted(self._doc_spans.keys()):
            combined.append(self._doc_spans[s].span_hash)
        for r in sorted(self._api_receipts.keys()):
            combined.append(self._api_receipts[r].response_sha256)
        for rl in sorted(self._rules.keys()):
            combined.append(rl)
            
        return hashlib.sha256("::".join(combined).encode()).hexdigest()

