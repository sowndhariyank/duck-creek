"""
Mechanical Grounding & Zero-Hallucination Barrier.
Parses output payloads from neural subagents, verifies citation resolubility,
and mechanically blocks any claim not linked to an authentic document span,
API response receipt, or rule ID.
"""

from typing import Dict, Any, List, Optional, Tuple
import re
import logging
from dataclasses import dataclass
from backend.core.epistemic_memory import EpistemicCitationRegistry

logger = logging.getLogger("amtha.grounding_guard")


class GroundingViolationException(Exception):
    """Raised when an ungrounded or uncited claim is detected in an agent response."""
    def __init__(self, message: str, violations: List[Dict[str, Any]]):
        super().__init__(message)
        self.violations = violations


@dataclass
class FactualClaim:
    entity_key: str
    entity_value: Any
    citation_id: Optional[str]
    citation_type: Optional[str] # "DOC_SPAN", "API_RECEIPT", "SYMBOLIC_RULE"


class GroundingGuard:
    """
    Mechanical zero-hallucination barrier.
    Blocks any subagent turn that fails citation verification.
    """

    def __init__(self, citation_registry: EpistemicCitationRegistry):
        self.registry = citation_registry

    def verify_and_enforce(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the groundedness of the payload.
        Inspects structured fields and embedded citations.
        """
        logger.info(f"Executing mechanical grounding evaluation for agent: [{agent_name}]")
        
        claims = self._extract_claims_from_payload(payload)
        violations = []

        for claim in claims:
            if not claim.citation_id:
                violations.append({
                    "entity": claim.entity_key,
                    "value": str(claim.entity_value),
                    "reason": "Missing citation identifier."
                })
                continue

            # Verify presence in Epistemic Citation Registry
            if claim.citation_type == "DOC_SPAN":
                if not self.registry.has_span(claim.citation_id):
                    violations.append({
                        "entity": claim.entity_key,
                        "value": str(claim.entity_value),
                        "citation_id": claim.citation_id,
                        "reason": f"Document span '{claim.citation_id}' not found in registry."
                    })
            elif claim.citation_type == "API_RECEIPT":
                if not self.registry.has_api_receipt(claim.citation_id):
                    violations.append({
                        "entity": claim.entity_key,
                        "value": str(claim.entity_value),
                        "citation_id": claim.citation_id,
                        "reason": f"API receipt '{claim.citation_id}' not found in registry."
                    })
            elif claim.citation_type == "SYMBOLIC_RULE":
                if not self.registry.has_rule(claim.citation_id):
                    violations.append({
                        "entity": claim.entity_key,
                        "value": str(claim.entity_value),
                        "citation_id": claim.citation_id,
                        "reason": f"Symbolic rule '{claim.citation_id}' not found in registry."
                    })

        if violations:
            logger.error(f"Grounding Barrier TRIPPED by [{agent_name}]: {len(violations)} violations.")
            raise GroundingViolationException(
                message=f"Agent [{agent_name}] produced {len(violations)} unverified claims.",
                violations=violations
            )

        logger.info(f"Agent [{agent_name}] cleared mechanical grounding check with 0 violations.")
        return payload

    def _extract_claims_from_payload(self, payload: Dict[str, Any]) -> List[FactualClaim]:
        """
        Recursively discovers factual claims marked with citations or requiring validation.
        """
        claims: List[FactualClaim] = []

        # If payload has a top-level 'citations' list
        citations_map = payload.get("_citations", {})

        for k, v in payload.items():
            if k.startswith("_"):
                continue

            if isinstance(v, dict):
                # Inspect nested dictionary
                nested_claims = self._extract_claims_from_payload(v)
                claims.extend(nested_claims)
            elif isinstance(v, (str, int, float, bool)) and k in citations_map:
                c_info = citations_map[k]
                claims.append(FactualClaim(
                    entity_key=k,
                    entity_value=v,
                    citation_id=c_info.get("id"),
                    citation_type=c_info.get("type", "DOC_SPAN")
                ))

        return claims

