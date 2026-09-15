"""
Apigee API Orchestration Interface & Mock Provider.
Provides an enterprise interface for hazard, geospatial, and credit feeds.
Supports Scott Hitchcock's pending-access trial environment with a high-fidelity mock.
"""

from abc import ABC, abstractmethod
import hashlib
import json
from typing import Dict, Any

class IApigeeOrchestrator(ABC):
    """Interface for Apigee-managed external insurance data services."""
    
    @abstractmethod
    async def fetch_hazard_risk_data(self, address: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Queries FEMA flood maps, wildfire indices, and earthquake hazard zones."""
        pass

    @abstractmethod
    async def fetch_iso_protection_class(self, address: str) -> Dict[str, Any]:
        """Queries ISO Public Protection Classification (PPC Grade 1-10)."""
        pass

    @abstractmethod
    async def fetch_commercial_credit_score(self, ein: str, company_name: str) -> Dict[str, Any]:
        """Queries commercial credit and financial stability indices."""
        pass


class MockApigeeOrchestrator(IApigeeOrchestrator):
    """
    Deterministic Local Mock Provider for Apigee Gateway.
    Generates realistic, grounded hazard and credit responses with SHA-256 payload receipts.
    """

    async def fetch_hazard_risk_data(self, address: str, latitude: float, longitude: float) -> Dict[str, Any]:
        if "Tahoe" in address or "CA" in address:
            flood_zone = "AE"
            wildfire_index = 8.8
            wildfire_tier = "Severe"
        elif "Seattle" in address or "WA" in address:
            flood_zone = "X"
            wildfire_index = 6.4
            wildfire_tier = "Elevated"
        else:
            flood_zone = "X"
            wildfire_index = 2.4
            wildfire_tier = "Low"

        payload = {
            "address": address,
            "coordinates": {"lat": latitude, "lon": longitude},
            "fema_flood_zone": flood_zone,
            "flood_zone_description": "FEMA Flood Insurance Rate Map (FIRM)",
            "wildfire_risk_index": wildfire_index,
            "wildfire_tier": wildfire_tier,
            "earthquake_fault_distance_miles": 22.5,
            "hurricane_wind_zone": "Zone_II",
            "service_provider": "Apigee_GIS_Hazard_Mesh_v2",
            "status": "SUCCESS"
        }
        payload_str = json.dumps(payload, sort_keys=True)
        payload["response_sha256"] = hashlib.sha256(payload_str.encode()).hexdigest()
        return payload

    async def fetch_iso_protection_class(self, address: str) -> Dict[str, Any]:
        ppc_grade = 4 if "WA" in address else (7 if "CA" in address else 3)
        payload = {
            "address": address,
            "iso_protection_class": ppc_grade,
            "hydrant_distance_feet": 450 if ppc_grade <= 4 else 1200,
            "responding_fire_station": "Municipal Fire Station #14",
            "station_distance_miles": 1.2 if ppc_grade <= 4 else 4.8,
            "service_provider": "Apigee_ISO_PPC_Connector",
            "status": "SUCCESS"
        }
        payload_str = json.dumps(payload, sort_keys=True)
        payload["response_sha256"] = hashlib.sha256(payload_str.encode()).hexdigest()
        return payload

    async def fetch_commercial_credit_score(self, ein: str, company_name: str) -> Dict[str, Any]:
        payload = {
            "ein": ein,
            "company_name": company_name,
            "commercial_credit_score": 82,
            "financial_stress_score": 1420,
            "paydex_score": 80,
            "bankruptcy_filings_count": 0,
            "service_provider": "Apigee_Credit_Insight_API",
            "status": "SUCCESS"
        }
        payload_str = json.dumps(payload, sort_keys=True)
        payload["response_sha256"] = hashlib.sha256(payload_str.encode()).hexdigest()
        return payload


def get_apigee_client(use_mock: bool = True) -> IApigeeOrchestrator:
    if use_mock:
        return MockApigeeOrchestrator()
    raise NotImplementedError("Live Apigee connection pending Scott Hitchcock trial provisioning.")
