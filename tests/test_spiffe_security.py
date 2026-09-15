"""
SPIFFE / Zero-Trust Tool Authorization Security Test Suite.
Verifies that agents are restricted to authorized tools and privilege escalation is blocked.
"""

import pytest
from backend.tools.spiffe_authorizer import (
    SpiffeToolAuthorizer,
    SpiffeSecurityViolationException
)

def test_authorized_tool_invocations():
    """Verifies that allowed subagent-tool pairs pass authorization checks."""
    assert SpiffeToolAuthorizer.validate_tool_invocation(
        "spiffe://amtha.net/agent/intake-doc",
        "docai_process_document_batch"
    ) is True
    
    assert SpiffeToolAuthorizer.validate_tool_invocation(
        "spiffe://amtha.net/agent/clearance-sanctions",
        "ofac_sdn_lookup"
    ) is True
    
    assert SpiffeToolAuthorizer.validate_tool_invocation(
        "spiffe://amtha.net/agent/data-enrichment",
        "apigee_hazard_zone_lookup"
    ) is True


def test_unauthorized_tool_call_blocked():
    """Verifies that an agent attempting to invoke an unauthorized tool is blocked."""
    # IntakeDocAgent trying to execute policy bind or ofac lookup
    with pytest.raises(SpiffeSecurityViolationException) as exc_info:
        SpiffeToolAuthorizer.validate_tool_invocation(
            "spiffe://amtha.net/agent/intake-doc",
            "state_store_transition" # Unauthorized tool
        )
    assert "is NOT authorized to execute tool" in str(exc_info.value)


def test_symbolic_rating_engine_has_zero_network_tools():
    """Verifies that the symbolic rating engine has NO authorized external network tools."""
    with pytest.raises(SpiffeSecurityViolationException):
        SpiffeToolAuthorizer.validate_tool_invocation(
            "spiffe://amtha.net/agent/symbolic-rating",
            "apigee_hazard_zone_lookup"
        )

