"""
Data Enrichment & External Hazard Specialist Agent.
Fetches external geospatial, FEMA flood, wildfire index, and ISO protection class data via Apigee.
"""

from typing import Dict, Any
import logging
from backend.interfaces.apigee_interface import IApigeeOrchestrator
from backend.core.epistemic_memory import EpistemicCitationRegistry
from backend.tools.spiffe_authorizer import SpiffeToolAuthorizer

logger = logging.getLogger("amtha.agents.enrichment")

class DataEnrichmentAgent:
    """Specialist subagent for geospatial hazard and credit data enrichment."""

    SPIFFE_ID = "spiffe://amtha.net/agent/data-enrichment"

    def __init__(self, apigee_client: IApigeeOrchestrator, registry: EpistemicCitationRegistry):
        self.apigee = apigee_client
        self.registry = registry

    async def execute(self, submission_id: str, address: str, ein: str) -> Dict[str, Any]:
        """Fetches hazard and PPC data, registering API receipts in memory."""
        SpiffeToolAuthorizer.validate_tool_invocation(self.SPIFFE_ID, "apigee_hazard_zone_lookup")
        
        hazard_data = await self.apigee.fetch_hazard_risk_data(address, latitude=30.2672, longitude=-97.7431)
        ppc_data = await self.apigee.fetch_iso_protection_class(address)
        credit_data = await self.apigee.fetch_commercial_credit_score(ein, "Apex Logistics Solutions")

        # Register API Receipts for Grounding
        receipt_hzr = self.registry.register_api_receipt(
            receipt_id=f"receipt_{submission_id}_hazard",
            service_name="Apigee Hazard Mesh",
            endpoint_url="/v1/hazards/lookup",
            response_sha256=hazard_data["response_sha256"],
            json_path="$.fema_flood_zone",
            value=hazard_data["fema_flood_zone"]
        )

        receipt_ppc = self.registry.register_api_receipt(
            receipt_id=f"receipt_{submission_id}_ppc",
            service_name="Apigee ISO PPC",
            endpoint_url="/v1/iso/ppc",
            response_sha256=ppc_data["response_sha256"],
            json_path="$.iso_protection_class",
            value=ppc_data["iso_protection_class"]
        )

        return {
            "agent_name": "data_enrichment_agent",
            "submission_id": submission_id,
            "fema_flood_zone": hazard_data["fema_flood_zone"],
            "wildfire_risk_index": hazard_data["wildfire_risk_index"],
            "iso_protection_class": ppc_data["iso_protection_class"],
            "commercial_credit_score": credit_data["commercial_credit_score"],
            "receipt_ids": [receipt_hzr.receipt_id, receipt_ppc.receipt_id],
            "message": f"Enrichment Complete: Flood Zone {hazard_data['fema_flood_zone']}, Wildfire {hazard_data['wildfire_risk_index']}, ISO PPC {ppc_data['iso_protection_class']}."
        }

