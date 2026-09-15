"""
SPIFFE / Agent Identity & Agent Gateway Tool Authorization.
Enforces least-privilege tool execution boundaries using down-scoped cryptographic identity tokens.
"""

from typing import Dict, Any, Set, Optional
import logging

logger = logging.getLogger("amtha.security.spiffe")

class SpiffeSecurityViolationException(Exception):
    """Raised when an agent attempts to invoke a tool beyond its SPIFFE authorization scope."""
    pass


# Strict Subagent -> Authorized Tools Capability Matrix
SUBAGENT_SPIFFE_CAPABILITIES: Dict[str, Set[str]] = {
    "spiffe://amtha.net/agent/intake-doc": {
        "gcs_read_submission_package", "docai_process_document_batch", "store_extracted_spans"
    },
    "spiffe://amtha.net/agent/clearance-sanctions": {
        "ofac_sdn_lookup", "cip_identity_verify", "bigquery_duplicate_submission_check"
    },
    "spiffe://amtha.net/agent/appetite-eligibility": {
        "naics_classifier_lookup", "appetite_rules_engine_query", "state_licensing_check"
    },
    "spiffe://amtha.net/agent/data-enrichment": {
        "apigee_hazard_zone_lookup", "apigee_iso_ppc_lookup", "apigee_financial_health_lookup"
    },
    "spiffe://amtha.net/agent/exposure-analysis": {
        "calculate_cope_metrics", "sov_aggregate_tiv", "pml_mfl_estimator"
    },
    "spiffe://amtha.net/agent/loss-history": {
        "parse_loss_run_table", "compute_loss_triangle_metrics"
    },
    "spiffe://amtha.net/agent/symbolic-rating": set(),  # Pure isolated in-memory compute - NO NETWORK TOOLS
    "spiffe://amtha.net/agent/quote-structuring": {
        "generate_quote_schedules", "apply_deductible_credits"
    },
    "spiffe://amtha.net/agent/grounding-compliance": {
        "ast_parse_claims", "verify_span_registry", "verify_rule_registry"
    },
    "spiffe://amtha.net/agent/triage-referral": {
        "authority_matrix_lookup", "generate_referral_brief"
    },
    "spiffe://amtha.net/agent/quote-lifecycle": {
        "state_store_transition", "quote_ttl_enforcer", "bind_order_generator"
    },
    "spiffe://amtha.net/agent/audit-governance": {
        "generate_merkle_root", "export_regulator_audit_bundle", "publish_looker_audit_metrics"
    },
    "spiffe://amtha.net/agent/supervisor": {
        # Supervisor can coordinate subagents but cannot directly invoke low-level sensitive tools
        "delegate_to_subagent", "render_a2ui_component"
    }
}


class SpiffeToolAuthorizer:
    """
    Agent Gateway & SPIFFE Identity Authorizer.
    Intercepts tool calls at the Envoy proxy layer.
    """

    @classmethod
    def validate_tool_invocation(cls, spiffe_id: str, tool_name: str) -> bool:
        """
        Validates whether the given SPIFFE identity is authorized to execute the requested tool.
        Throws SpiffeSecurityViolationException if unauthorized.
        """
        allowed_tools = SUBAGENT_SPIFFE_CAPABILITIES.get(spiffe_id, set())
        
        if tool_name not in allowed_tools:
            logger.warning(
                f"SECURITY ALERT: Unauthorized tool invocation attempt: [{spiffe_id}] -> [{tool_name}]"
            )
            raise SpiffeSecurityViolationException(
                f"Agent with SPIFFE identity '{spiffe_id}' is NOT authorized to execute tool '{tool_name}'."
            )
            
        logger.debug(f"Authorized tool execution: [{spiffe_id}] -> [{tool_name}]")
        return True
