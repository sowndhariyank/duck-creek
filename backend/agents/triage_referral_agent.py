"""
Triage & Referral Routing Specialist Agent.
Deterministically compares risk scores and exposures against underwriting authority matrices.
Routes to Straight-Through Processing (STP) or generates an actionable Underwriter Referral Brief.
"""

from typing import Dict, Any, List, Optional
import logging
from backend.tools.spiffe_authorizer import SpiffeToolAuthorizer

logger = logging.getLogger("amtha.agents.triage")

class TriageReferralAgent:
    """Specialist subagent for STP vs Referral queue triage."""

    SPIFFE_ID = "spiffe://amtha.net/agent/triage-referral"

    def execute(
        self,
        submission_id: str,
        risk_score: int,
        tiv: float,
        appetite_tier: str,
        wildfire_index: float,
        flood_zone: str,
        open_claims: int
    ) -> Dict[str, Any]:
        """Evaluates STP auto-release criteria vs Human-in-the-Loop referral."""
        SpiffeToolAuthorizer.validate_tool_invocation(self.SPIFFE_ID, "authority_matrix_lookup")

        # Straight-Through Processing (STP) Rule
        is_stp = (
            risk_score >= 85 and
            appetite_tier == "PREFERRED" and
            tiv <= 15000000.0 and
            wildfire_index <= 5.0 and
            flood_zone in ["X", "C"] and
            open_claims == 0
        )

        referral_brief: Optional[Dict[str, Any]] = None

        if is_stp:
            decision = "STRAIGHT_THROUGH_AUTO_QUOTE"
            authority_required = "AUTO_RELEASE"
            message = f"STP Approved: Risk Score {risk_score}/100 meets all straight-through binding thresholds."
        elif risk_score >= 60:
            decision = "HUMAN_UNDERWRITER_REFERRAL"
            authority_required = "UNDERWRITER_II"
            
            # Compile Underwriter Brief
            triggers: List[str] = []
            if tiv > 15000000.0:
                triggers.append(f"TIV of ${tiv:,.2f} exceeds standard $15M automated limit.")
            if wildfire_index > 5.0:
                triggers.append(f"Wildfire risk index ({wildfire_index}) requires perimeter vegetation review.")
            if flood_zone not in ["X", "C"]:
                triggers.append(f"Flood zone '{flood_zone}' requires separate flood underwriting sublimit.")
            if open_claims > 0:
                triggers.append(f"Account has {open_claims} active open claims requiring loss review.")

            referral_brief = {
                "submission_id": submission_id,
                "risk_score": risk_score,
                "assigned_authority": authority_required,
                "primary_triggers": triggers or [f"Risk score {risk_score} in standard referral band."],
                "recommended_conditions": [
                    "Prior to Bind: Confirm building electrical certification.",
                    "Coverage: Apply $5,000 separate Wind/Hail deductible."
                ]
            }
            message = f"Referred to Underwriting Desk ({authority_required}): {len(referral_brief['primary_triggers'])} triggers identified."
        else:
            decision = "AUTO_DECLINE"
            authority_required = "SENIOR_UNDERWRITER_II"
            message = f"Submission Declined: Risk Score {risk_score}/100 is below minimum acceptable threshold (60)."

        return {
            "agent_name": "triage_referral_agent",
            "submission_id": submission_id,
            "routing_decision": decision,
            "authority_required": authority_required,
            "is_stp": is_stp,
            "referral_brief": referral_brief,
            "message": message
        }

