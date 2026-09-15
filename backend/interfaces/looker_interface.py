"""
Looker Semantic Layer & Analytics Interface.
Provides unified semantic queries for underwriter benchmarks and dashboard embedding.
Supports Scott Hitchcock's pending-access trial environment with a deterministic mock.
"""

from abc import ABC, abstractmethod
import json
import hashlib
from typing import Dict, Any

class ILookerAnalytics(ABC):
    """Interface for Looker semantic models and portfolio metrics."""

    @abstractmethod
    async def query_portfolio_loss_ratio(self, naics_code: str, territory: str) -> Dict[str, Any]:
        """Queries historical industry loss ratio benchmarks from the Looker semantic layer."""
        pass

    @abstractmethod
    async def generate_dashboard_embed_url(self, session_id: str, underwriter_id: str) -> Dict[str, Any]:
        """Generates a secure embed URL for real-time portfolio analytics dashboards."""
        pass


class MockLookerAnalytics(ILookerAnalytics):
    """Deterministic local mock for Looker Semantic Layer."""

    async def query_portfolio_loss_ratio(self, naics_code: str, territory: str) -> Dict[str, Any]:
        data = {
            "naics_code": naics_code,
            "industry_title": "Custom Computer Programming / IT Logistics",
            "territory": territory,
            "5yr_industry_average_loss_ratio": 0.442,
            "top_quartile_loss_ratio": 0.185,
            "territory_hazard_spread": 0.082,
            "semantic_model_version": "looker_uw_core_v4.2"
        }
        data["query_hash"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        return data

    async def generate_dashboard_embed_url(self, session_id: str, underwriter_id: str) -> Dict[str, Any]:
        return {
            "embed_url": f"https://looker.amtha.internal/embed/dashboards/underwriter_workbench?session={session_id}&user={underwriter_id}",
            "expires_in_seconds": 3600,
            "status": "READY"
        }


def get_looker_client(use_mock: bool = True) -> ILookerAnalytics:
    """Factory method to resolve the active Looker client."""
    if use_mock:
        return MockLookerAnalytics()
    raise NotImplementedError("Live Looker connection pending Scott Hitchcock trial provisioning.")

