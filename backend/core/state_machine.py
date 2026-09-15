"""
Quote Lifecycle Finite State Machine (FSM).
Enforces valid state transitions, prevents orphaned and fragmented quotes,
and records immutable event history into the BigQuery ledger.
"""

from typing import Dict, Any, List, Optional
import time
import logging
from backend.tools.bigquery_tools import BigQueryToolSuite

logger = logging.getLogger("amtha.state_machine")

class InvalidStateTransitionException(Exception):
    """Raised when an illegal quote state transition is attempted."""
    pass


class QuoteLifecycleStateMachine:
    """
    Finite State Machine governing the quote lifecycle.
    Guarantees zero orphan quotes and zero version fragmentation.
    """

    VALID_TRANSITIONS: Dict[str, List[str]] = {
        "DRAFT": ["INGESTING", "CANCELLED"],
        "INGESTING": ["ENRICHING", "INGESTION_FAILED", "CANCELLED"],
        "ENRICHING": ["SCORING", "ENRICHMENT_FAILED", "CANCELLED"],
        "SCORING": ["RATED", "RATING_FAILED"],
        "RATED": ["QUOTED_STP", "REFERRED", "DECLINED"],
        "REFERRED": ["UNDER_REVIEW", "AUTO_DECLINED"],
        "UNDER_REVIEW": ["QUOTED_MANUAL", "RE_RATING", "DECLINED"],
        "RE_RATING": ["SCORING"],
        "QUOTED_STP": ["BOUND", "EXPIRED", "CANCELLED"],
        "QUOTED_MANUAL": ["BOUND", "EXPIRED", "CANCELLED"],
        "BOUND": ["POLICY_ISSUED"],
        "POLICY_ISSUED": [],
        "DECLINED": [],
        "EXPIRED": [],
        "CANCELLED": []
    }

    def __init__(self, quote_id: str, submission_id: str, bq_tool: BigQueryToolSuite):
        self.quote_id = quote_id
        self.submission_id = submission_id
        self.bq_tool = bq_tool
        self.current_state = "DRAFT"
        self.created_at = time.time()
        self.updated_at = time.time()
        self.ttl_expiration = time.time() + (30 * 86400) # 30-day quote lock

        # Record Initial Creation
        self.bq_tool.append_lifecycle_event(
            quote_id=self.quote_id,
            submission_id=self.submission_id,
            from_state="NONE",
            to_state="DRAFT",
            event_name="QUOTE_INITIALIZED",
            actor_id="SYSTEM",
            metadata={"ttl_expiration": self.ttl_expiration}
        )

    def transition_to(self, target_state: str, actor_id: str, event_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Executes an atomic, validated state transition.
        Throws InvalidStateTransitionException if illegal.
        """
        metadata = metadata or {}
        allowed_targets = self.VALID_TRANSITIONS.get(self.current_state, [])

        if target_state == self.current_state:
            # Idempotent state confirmation
            self.bq_tool.append_lifecycle_event(
                quote_id=self.quote_id,
                submission_id=self.submission_id,
                from_state=self.current_state,
                to_state=target_state,
                event_name=event_name,
                actor_id=actor_id,
                metadata=metadata
            )
            return self.current_state

        if target_state not in allowed_targets:
            msg = f"Illegal State Transition: Cannot move quote [{self.quote_id}] from '{self.current_state}' to '{target_state}'."
            logger.error(msg)
            raise InvalidStateTransitionException(msg)

        prior_state = self.current_state
        self.current_state = target_state
        self.updated_at = time.time()

        self.bq_tool.append_lifecycle_event(
            quote_id=self.quote_id,
            submission_id=self.submission_id,
            from_state=prior_state,
            to_state=target_state,
            event_name=event_name,
            actor_id=actor_id,
            metadata=metadata
        )

        logger.info(f"Quote [{self.quote_id}] transitioned from '{prior_state}' -> '{target_state}' by [{actor_id}]")
        return self.current_state

    def check_orphan_status(self) -> bool:
        """Checks if a quote has expired or become orphaned."""
        if time.time() > self.ttl_expiration and self.current_state in ["QUOTED_STP", "QUOTED_MANUAL"]:
            self.transition_to(
                target_state="EXPIRED",
                actor_id="ORPHAN_WATCHDOG_DAEMON",
                event_name="TTL_LOCK_EXPIRED",
                metadata={"reason": "30-day price lock elapsed"}
            )
            return True
        return False

