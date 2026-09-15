"""
Appetite & Eligibility Specialist Agent.
Matches applicant operations and NAICS codes against underwriting appetite guidelines.
"""

from typing import Dict, Any
import logging
from backend.tools.spiffe_authorizer import SpiffeToolAuthorizer

logger = logging.getLogger("amtha.agents.appetite")

class AppetiteEligibilityAgent:
    """Specialist subagent for underwriting eligibility and NAICS mapping."""

    SPIFFE_ID = "spiffe://amtha.net/agent/appetite-eligibility"

    def execute(self, submission_id: str, business_description: str, naics_code: str) -> Dict[str, Any]:
        """Evaluates underwriting appetite criteria."""
        SpiffeToolAuthorizer.validate_tool_invocation(self.SPIFFE_ID, "appetite_rules_engine_query")
        
        # Determine appetite tier
        if naics_code in ["541512", "541511"]: # IT & Software
            tier = "PREFERRED"
            eligible = True
            rule_id = "RULE-APPETITE-IT-PREFERRED"
        elif naics_code in ["493110"]: # Warehousing
            tier = "STANDARD"
            eligible = True
            rule_id = "RULE-APPETITE-WAREHOUSE-STD"
        elif naics_code in ["236220"]: # Construction
            tier = "SPECIALTY_REFERRAL"
            eligible = True
            rule_id = "RULE-APPETITE-CONST-REFERRAL"
        else:
            tier = "STANDARD"
            eligible = True
            rule_id = "RULE-APPETITE-GEN-STD"

        return {
            "agent_name": "appetite_eligibility_agent",
            "submission_id": submission_id,
            "naics_code": naics_code,
            "appetite_tier": tier,
            "eligible": eligible,
            "rule_id": rule_id,
            "message": f"Appetite Confirmed: NAICS {naics_code} classified as {tier} risk under {rule_id}."
        }

