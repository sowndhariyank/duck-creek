"""
Quote Lifecycle FSM & Anti-Orphan Test Suite.
Validates state transitions, illegal transition blocks, and durable BigQuery ledger event recording.
"""

import pytest
import time
from backend.core.state_machine import QuoteLifecycleStateMachine, InvalidStateTransitionException
from backend.tools.bigquery_tools import BigQueryToolSuite

@pytest.fixture
def fsm_instance():
    bq = BigQueryToolSuite()
    fsm = QuoteLifecycleStateMachine(quote_id="Q-TEST-101", submission_id="SUB-101", bq_tool=bq)
    return fsm, bq

def test_valid_lifecycle_progression(fsm_instance):
    fsm, bq = fsm_instance
    
    assert fsm.current_state == "DRAFT"
    
    # Valid progression: DRAFT -> INGESTING -> ENRICHING -> SCORING -> RATED -> QUOTED_STP -> BOUND -> POLICY_ISSUED
    fsm.transition_to("INGESTING", actor_id="orchestrator", event_name="DOC_AI_START")
    assert fsm.current_state == "INGESTING"
    
    fsm.transition_to("ENRICHING", actor_id="orchestrator", event_name="ENRICHMENT_START")
    assert fsm.current_state == "ENRICHING"
    
    fsm.transition_to("SCORING", actor_id="orchestrator", event_name="SCORING_START")
    assert fsm.current_state == "SCORING"
    
    fsm.transition_to("RATED", actor_id="symbolic_engine", event_name="RATED_DONE")
    assert fsm.current_state == "RATED"
    
    fsm.transition_to("QUOTED_STP", actor_id="triage_agent", event_name="STP_RELEASE")
    assert fsm.current_state == "QUOTED_STP"
    
    fsm.transition_to("BOUND", actor_id="broker_user", event_name="QUOTE_BOUND")
    assert fsm.current_state == "BOUND"
    
    fsm.transition_to("POLICY_ISSUED", actor_id="pas_system", event_name="POLICY_ACTIVE")
    assert fsm.current_state == "POLICY_ISSUED"
    
    # Verify BigQuery ledger contains all transition events
    history = bq.get_quote_history("Q-TEST-101")
    assert len(history) == 8 # 1 init + 7 transitions


def test_illegal_state_transition_blocked(fsm_instance):
    fsm, _ = fsm_instance
    
    # Attempting illegal jump: DRAFT -> BOUND directly
    with pytest.raises(InvalidStateTransitionException) as exc_info:
        fsm.transition_to("BOUND", actor_id="malicious_actor", event_name="ILLEGAL_BIND")
        
    assert "Illegal State Transition" in str(exc_info.value)
    assert fsm.current_state == "DRAFT"


def test_orphan_watchdog_detection(fsm_instance):
    fsm, _ = fsm_instance
    
    # Move to QUOTED_STP
    fsm.transition_to("INGESTING", actor_id="system", event_name="START")
    fsm.transition_to("ENRICHING", actor_id="system", event_name="ENRICH")
    fsm.transition_to("SCORING", actor_id="system", event_name="SCORE")
    fsm.transition_to("RATED", actor_id="system", event_name="RATE")
    fsm.transition_to("QUOTED_STP", actor_id="system", event_name="QUOTE")
    
    # Simulate TTL expiration in the past
    fsm.ttl_expiration = time.time() - 100
    
    is_orphaned = fsm.check_orphan_status()
    assert is_orphaned is True
    assert fsm.current_state == "EXPIRED"

