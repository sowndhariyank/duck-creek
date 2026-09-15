"""
Exposure & COPE Analysis Specialist Agent.
Evaluates Construction, Occupancy, Protection, and Exposure metrics with Probable Maximum Loss (PML).
"""

from typing import Dict, Any
import logging
from backend.tools.spiffe_authorizer import SpiffeToolAuthorizer

logger = logging.getLogger("amtha.agents.exposure")

class ExposureAnalysisAgent:
    """Specialist subagent for COPE property decomposition."""

    SPIFFE_ID = "spiffe://amtha.net/agent/exposure-analysis"

    def execute(
        self,
        submission_id: str,
        tiv: float,
        construction_type: str,
        sprinklered: bool,
        roof_age_years: int
    ) -> Dict[str, Any]:
        """Calculates COPE risk profile and PML estimate."""
        SpiffeToolAuthorizer.validate_tool_invocation(self.SPIFFE_ID, "calculate_cope_metrics")
        
        # PML estimation
        pml_pct = 0.25 if sprinklered else 0.65
        pml_dollars = round(tiv * pml_pct, 2)
        
        return {
            "agent_name": "exposure_analysis_agent",
            "submission_id": submission_id,
            "total_insured_value": tiv,
            "construction_class": construction_type,
            "protection_grade": "100% NFPA 13 Wet Sprinklers" if sprinklered else "Unsprinklered",
            "roof_condition": f"Age {roof_age_years} Years (Optimal)" if roof_age_years <= 10 else f"Age {roof_age_years} Years (Aging)",
            "pml_percentage": pml_pct * 100.0,
            "pml_dollar_amount": pml_dollars,
            "exposure_tier": "LOW_EXPOSURE",
            "message": f"COPE Evaluation Completed: TIV ${tiv:,.2f}, Estimated PML ${pml_dollars:,.2f} ({pml_pct*100:.0f}%)."
        }

