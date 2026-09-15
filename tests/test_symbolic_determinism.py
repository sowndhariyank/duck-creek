"""
Symbolic Rating Engine Invariance & Determinism Verification Suite.
Validates the Zero-LLM Invariant across 10,000 randomized and edge-case permutations.
Asserts 100.0% bitwise reproducibility on re-execution.
"""

import pytest
import random
from backend.agents.symbolic_rating_engine import SymbolicRatingEngine, RULE_SET_VERSION

def test_single_deterministic_trace_reproducibility():
    """Verifies that running the same input twice produces identical decision hashes and outputs."""
    engine = SymbolicRatingEngine(rule_version="v2026.3")
    
    input_params = {
        "submission_id": "SUB-TEST-001",
        "naics_code": "541512",
        "tiv": 12500000.0,
        "annual_revenue": 8500000.0,
        "construction_type": "Masonry_Non_Combustible",
        "ppc_grade": 3,
        "flood_zone": "X",
        "wildfire_index": 2.4,
        "sprinklered": True,
        "building_age_years": 8,
        "roof_age_years": 6,
        "five_year_incurred_losses": 0.0,
        "open_claims_count": 0,
        "territory_factor": 1.05,
        "schedule_credit_debit": -0.05
    }
    
    res1 = engine.evaluate_submission(**input_params)
    res2 = engine.evaluate_submission(**input_params)
    
    assert res1["decision_hash"] == res2["decision_hash"]
    assert res1["underwriting_risk_score"] == res2["underwriting_risk_score"]
    assert res1["property_premium"] == res2["property_premium"]
    assert res1["gl_premium"] == res2["gl_premium"]
    assert res1["total_base_premium"] == res2["total_base_premium"]
    assert len(res1["decision_trace"]) == len(res2["decision_trace"])
    assert res1["risk_tier"] == "PREFERRED_STP"


def test_10000_iterations_determinism_stress():
    """
    Stress-tests the deterministic invariant across 10,000 pseudorandom submissions.
    Ensures zero stochastic drift.
    """
    engine = SymbolicRatingEngine(rule_version="v2026.3")
    
    naics_options = ["541512", "493110", "236220", "DEFAULT"]
    const_options = ["Frame", "Joisted_Masonry", "Non_Combustible", "Masonry_Non_Combustible", "Modified_Fire_Resistive", "Fire_Resistive"]
    flood_options = ["X", "C", "AE", "A", "VE", "V"]
    
    # Use fixed seed for repeatable test suite
    rng = random.Random(42)
    
    test_batch = []
    for i in range(10000):
        params = {
            "submission_id": f"SUB-SIM-{i}",
            "naics_code": rng.choice(naics_options),
            "tiv": round(rng.uniform(500000, 50000000), 2),
            "annual_revenue": round(rng.uniform(200000, 30000000), 2),
            "construction_type": rng.choice(const_options),
            "ppc_grade": rng.randint(1, 10),
            "flood_zone": rng.choice(flood_options),
            "wildfire_index": round(rng.uniform(1.0, 10.0), 1),
            "sprinklered": rng.choice([True, False]),
            "building_age_years": rng.randint(1, 60),
            "roof_age_years": rng.randint(1, 35),
            "five_year_incurred_losses": round(rng.uniform(0, 200000), 2) if rng.random() > 0.5 else 0.0,
            "open_claims_count": rng.randint(0, 3) if rng.random() > 0.7 else 0,
            "territory_factor": round(rng.uniform(0.90, 1.30), 2),
            "schedule_credit_debit": round(rng.uniform(-0.35, 0.35), 2)
        }
        test_batch.append(params)
    
    # Run first pass
    hashes_pass_1 = [engine.evaluate_submission(**p)["decision_hash"] for p in test_batch]
    # Run second pass
    hashes_pass_2 = [engine.evaluate_submission(**p)["decision_hash"] for p in test_batch]
    
    assert hashes_pass_1 == hashes_pass_2, "Non-deterministic execution detected across 10,000 iterations!"
    assert len(hashes_pass_1) == 10000


def test_statutory_schedule_credit_bounds():
    """Ensures schedule credits/debits never breach the statutory +/- 25% boundary."""
    engine = SymbolicRatingEngine()
    
    res_high = engine.evaluate_submission(
        submission_id="SUB-BOUND-1",
        naics_code="541512",
        tiv=1000000.0,
        annual_revenue=1000000.0,
        construction_type="Non_Combustible",
        ppc_grade=3,
        flood_zone="X",
        wildfire_index=1.0,
        sprinklered=True,
        building_age_years=5,
        roof_age_years=5,
        five_year_incurred_losses=0.0,
        open_claims_count=0,
        schedule_credit_debit=0.85 # Extreme out-of-bounds request
    )
    
    # Check that in the decision trace, c_sched was clamped to 0.25
    sched_step = [s for s in res_high["decision_trace"] if s["step_name"] == "ScheduleRatingAdjustment"][0]
    assert sched_step["output"]["c_sched"] == 0.25


def test_emod_clamping_bounds():
    """Ensures Experience Modifier is strictly clamped within [0.70, 1.40]."""
    engine = SymbolicRatingEngine()
    
    # Massive losses that would blow past 2.0 without cap
    res_loss = engine.evaluate_submission(
        submission_id="SUB-EMOD-1",
        naics_code="541512",
        tiv=500000.0,
        annual_revenue=500000.0,
        construction_type="Non_Combustible",
        ppc_grade=3,
        flood_zone="X",
        wildfire_index=1.0,
        sprinklered=False,
        building_age_years=10,
        roof_age_years=10,
        five_year_incurred_losses=5000000.0, # $5M loss on small policy
        open_claims_count=2
    )
    
    emod_step = [s for s in res_loss["decision_trace"] if s["step_name"] == "ExperienceModifier"][0]
    assert emod_step["output"]["emod"] == 1.40
    assert res_loss["risk_tier"] == "REFERRAL_REQUIRED"
    assert res_loss["underwriting_risk_score"] == 65

def test_decline_tier_evaluation():
    """Ensures severely impaired risk is evaluated as DECLINE tier."""
    engine = SymbolicRatingEngine()
    
    res_decline = engine.evaluate_submission(
        submission_id="SUB-DECLINE-1",
        naics_code="541512",
        tiv=500000.0,
        annual_revenue=500000.0,
        construction_type="Frame", # -12
        ppc_grade=9, # -20
        flood_zone="AE", # -15
        wildfire_index=8.8, # -15
        sprinklered=False,
        building_age_years=40,
        roof_age_years=25, # -15
        five_year_incurred_losses=500000.0, # -25
        open_claims_count=2 # -15
    )
    assert res_decline["risk_tier"] == "DECLINE"
    assert res_decline["underwriting_risk_score"] == 0
