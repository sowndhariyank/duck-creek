"""
Quote Lifecycle Specialist Agent.
Interacts with the QuoteLifecycleStateMachine to persist quote versions and trigger bind orders.
"""

from typing import Dict, Any, Optional
import logging
from backend.core.state_machine import QuoteLifecycleStateMachine
from backend.tools.spiffe_authorizer import SpiffeToolAuthorizer

logger = logging.getLogger("amtha.agents.lifecycle")

class QuoteLifecycleAgent:
    """Specialist subagent for quote lifecycle persistence and anti-orphan state management."""

    SPIFFE_ID = "spiffe://amtha.net/agent/quote-lifecycle"

    def execute(
        self,
        fsm: QuoteLifecycleStateMachine,
        target_state: str,
        actor_id: str,
        event_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transitions quote state with SPIFFE authorization."""
        SpiffeToolAuthorizer.validate_tool_invocation(self.SPIFFE_ID, "state_store_transition")
        
        new_state = fsm.transition_to(
            target_state=target_state,
            actor_id=actor_id,
            event_name=event_name,
            metadata=metadata
        )
        
        return {
            "agent_name": "quote_lifecycle_agent",
            "quote_id": fsm.quote_id,
            "submission_id": fsm.submission_id,
            "current_state": new_state,
            "ttl_expiration_timestamp": fsm.ttl_expiration,
            "is_orphaned": False,
            "message": f"Quote [{fsm.quote_id}] state successfully advanced to '{new_state}'."
        }

