"""
Symbolic Rating Engine (Zero-LLM Actuarial Core).
Executes deterministic rating formulas, risk score calculations, and multi-tier quote generation.
Zero stochastic operations, zero LLM calls. Fully auditable decision trace.
"""

from typing import Dict, Any, List, Optional
import hashlib
import json
import decimal
from decimal import Decimal, ROUND_HALF_UP

# Actuarial Rule Set Version
RULE_SET_VERSION = "v2026.3"

# Lookup Tables
ISO_CONSTRUCTION_FACTORS: Dict[str, float] = {
    "Frame": 1.45,
    "Joisted_Masonry": 1.20,
    "Non_Combustible": 1.00,
    "Masonry_Non_Combustible": 0.85,
    "Modified_Fire_Resistive": 0.70,
    "Fire_Resistive": 0.55
}

ISO_PPC_FACTORS: Dict[int, float] = {
    1: 0.85, 2: 0.85,
    3: 0.95, 4: 0.95,
    5: 1.10, 6: 1.10,
    7: 1.30, 8: 1.30,
    9: 1.65, 10: 1.65
}

FEMA_FLOOD_FACTORS: Dict[str, float] = {
    "X": 1.00,
    "C": 1.00,
    "AE": 1.45,
    "A": 1.45,
    "VE": 2.20,
    "V": 2.20
}

NAICS_BASE_RATES: Dict[str, Dict[str, float]] = {
    "541512": {"prop_base_rate": 0.28, "gl_base_rate": 3.80, "expected_loss_rate": 0.0022}, # IT / Software
    "493110": {"prop_base_rate": 0.45, "gl_base_rate": 6.20, "expected_loss_rate": 0.0040}, # General Warehousing
    "236220": {"prop_base_rate": 0.55, "gl_base_rate": 9.50, "expected_loss_rate": 0.0065}, # Commercial Building Construction
    "DEFAULT": {"prop_base_rate": 0.35, "gl_base_rate": 4.50, "expected_loss_rate": 0.0030}
}


class SymbolicRatingEngine:
    """
    Pure Symbolic Rating & Scoring Engine.
    Guarantees 100% bitwise determinism and full regulatory auditability.
    """

    def __init__(self, rule_version: str = RULE_SET_VERSION):
        self.rule_version = rule_version

    def evaluate_submission(
        self,
        submission_id: str,
        naics_code: str,
        tiv: float,
        annual_revenue: float,
        construction_type: str,
        ppc_grade: int,
        flood_zone: str,
        wildfire_index: float,
        sprinklered: bool,
        building_age_years: int,
        roof_age_years: int,
        five_year_incurred_losses: float,
        open_claims_count: int,
        territory_factor: float = 1.05,
        schedule_credit_debit: float = 0.0
    ) -> Dict[str, Any]:
        """
        Executes deterministic rating and scoring logic.
        Produces risk score, breakdown, multi-tier quotes, and complete decision trace.
        """
        steps_log: List[Dict[str, Any]] = []

        # 1. Base Rate Lookup
        rates = NAICS_BASE_RATES.get(naics_code, NAICS_BASE_RATES["DEFAULT"])
        prop_base_rate = rates["prop_base_rate"]
        gl_base_rate = rates["gl_base_rate"]
        expected_loss_rate = rates["expected_loss_rate"]

        steps_log.append({
            "step_index": 1,
            "step_name": "BaseRateLookup",
            "rule_id": f"RULE-BASE-{naics_code}",
            "variables": {"naics": naics_code, "prop_base_rate": prop_base_rate, "gl_base_rate": gl_base_rate},
            "output": {"prop_base": prop_base_rate, "gl_base": gl_base_rate}
        })

        # 2. Construction Factor
        f_const = ISO_CONSTRUCTION_FACTORS.get(construction_type, 1.00)
        steps_log.append({
            "step_index": 2,
            "step_name": "ConstructionFactor",
            "rule_id": f"RULE-CONST-{construction_type.upper()}",
            "variables": {"construction_type": construction_type},
            "output": {"f_const": f_const}
        })

        # 3. Protection Class Factor
        f_prot = ISO_PPC_FACTORS.get(ppc_grade, 1.00)
        steps_log.append({
            "step_index": 3,
            "step_name": "ProtectionClassFactor",
            "rule_id": f"RULE-PPC-GRADE-{ppc_grade}",
            "variables": {"ppc_grade": ppc_grade},
            "output": {"f_prot": f_prot}
        })

        # 4. Catastrophe Factors
        f_flood = FEMA_FLOOD_FACTORS.get(flood_zone.upper(), 1.00)
        f_wildfire = 1.00
        if wildfire_index > 8.5:
            f_wildfire = 2.10
        elif wildfire_index > 6.0:
            f_wildfire = 1.50
        elif wildfire_index > 3.0:
            f_wildfire = 1.15

        f_cat = round(f_flood * f_wildfire, 4)
        steps_log.append({
            "step_index": 4,
            "step_name": "CatastropheFactor",
            "rule_id": "RULE-CAT-COMPOSITE",
            "variables": {"flood_zone": flood_zone, "f_flood": f_flood, "wildfire_index": wildfire_index, "f_wildfire": f_wildfire},
            "output": {"f_cat": f_cat}
        })

        # 5. Experience Rating Modifier (E-Mod)
        expected_losses = tiv * expected_loss_rate
        ballast_k = 50000.0
        emod_raw = 1.0 + (five_year_incurred_losses - expected_losses) / (expected_losses + ballast_k)
        emod = round(max(0.70, min(1.40, emod_raw)), 4)
        steps_log.append({
            "step_index": 5,
            "step_name": "ExperienceModifier",
            "rule_id": "RULE-EMOD-5YR",
            "variables": {
                "incurred_losses": five_year_incurred_losses,
                "expected_losses": expected_losses,
                "ballast_k": ballast_k,
                "emod_raw": emod_raw
            },
            "output": {"emod": emod}
        })

        # 6. Schedule Rating Adjustments (Bounded to +/- 0.25)
        c_sched = max(-0.25, min(0.25, schedule_credit_debit))
        steps_log.append({
            "step_index": 6,
            "step_name": "ScheduleRatingAdjustment",
            "rule_id": "RULE-SCHED-ADJ",
            "variables": {"requested_adjustment": schedule_credit_debit},
            "output": {"c_sched": c_sched}
        })

        # 7. Property Technical Premium Calculation
        # Formula: (TIV / 100) * BaseRate * F_terr * F_const * F_prot * F_cat * E_mod * (1 + C_sched)
        prop_prem_raw = (tiv / 100.0) * prop_base_rate * territory_factor * f_const * f_prot * f_cat * emod * (1.0 + c_sched)
        property_premium = round(prop_prem_raw, 2)

        # 8. General Liability Premium Calculation
        gl_prem_raw = (annual_revenue / 1000.0) * gl_base_rate * territory_factor * emod * (1.0 + c_sched)
        gl_premium = round(gl_prem_raw, 2)

        total_base_premium = round(property_premium + gl_premium, 2)

        steps_log.append({
            "step_index": 7,
            "step_name": "PremiumCalculation",
            "rule_id": "RULE-PREM-COMBINED",
            "variables": {
                "tiv": tiv,
                "annual_revenue": annual_revenue,
                "prop_base_rate": prop_base_rate,
                "gl_base_rate": gl_base_rate,
                "territory_factor": territory_factor,
                "f_const": f_const,
                "f_prot": f_prot,
                "f_cat": f_cat,
                "emod": emod,
                "c_sched": c_sched
            },
            "output": {
                "property_premium": property_premium,
                "gl_premium": gl_premium,
                "total_base_premium": total_base_premium
            }
        })

        # 9. Deterministic Risk Scoring (0 - 100)
        score = 100
        credits_applied = []
        penalties_applied = []

        if sprinklered:
            score += 10
            credits_applied.append({"factor": "NFPA 13 Sprinklers", "pts": 10})
        if five_year_incurred_losses == 0:
            score += 8
            credits_applied.append({"factor": "5-Yr Loss Free Track", "pts": 8})
        if building_age_years <= 10:
            score += 5
            credits_applied.append({"factor": "Modern Facility (<10 Yrs)", "pts": 5})

        if construction_type == "Frame":
            score -= 12
            penalties_applied.append({"factor": "Frame Construction", "pts": -12})
        elif construction_type == "Joisted_Masonry":
            score -= 6
            penalties_applied.append({"factor": "Joisted Masonry Construction", "pts": -6})

        if ppc_grade >= 7:
            score -= 10
            penalties_applied.append({"factor": f"PPC Grade {ppc_grade}", "pts": -10})

        if roof_age_years > 20:
            score -= 15
            penalties_applied.append({"factor": f"Roof Age ({roof_age_years} yrs)", "pts": -15})
        elif roof_age_years > 15:
            score -= 8
            penalties_applied.append({"factor": f"Roof Age ({roof_age_years} yrs)", "pts": -8})

        if flood_zone in ["AE", "A"]:
            score -= 15
            penalties_applied.append({"factor": f"Special Flood Hazard {flood_zone}", "pts": -15})

        if wildfire_index > 6.0:
            score -= 15
            penalties_applied.append({"factor": f"High Wildfire Index {wildfire_index}", "pts": -15})

        if five_year_incurred_losses > 100000:
            score -= 25
            penalties_applied.append({"factor": "Severe Loss History (> $100k)", "pts": -25})
        elif five_year_incurred_losses > 25000:
            score -= 12
            penalties_applied.append({"factor": "Moderate Loss History", "pts": -12})
        elif five_year_incurred_losses > 0:
            score -= 4
            penalties_applied.append({"factor": "Minor Prior Loss", "pts": -4})

        if open_claims_count > 0:
            score -= 15
            penalties_applied.append({"factor": f"Active Open Claims ({open_claims_count})", "pts": -15})

        final_score = max(0, min(100, score))

        if final_score >= 85:
            tier = "PREFERRED_STP"
        elif final_score >= 70:
            tier = "STANDARD"
        elif final_score >= 60:
            tier = "REFERRAL_REQUIRED"
        else:
            tier = "DECLINE"

        steps_log.append({
            "step_index": 8,
            "step_name": "UnderwritingScoreEvaluation",
            "rule_id": "RULE-SCORE-2026",
            "variables": {"credits": credits_applied, "penalties": penalties_applied},
            "output": {"score": final_score, "tier": tier}
        })

        # 10. Multi-Tier Quote Option Structuring
        quote_options = [
            {
                "tier_name": "Basic",
                "annual_premium": round(total_base_premium * 0.88, 2),
                "property_limit": tiv,
                "gl_limit": "$1M / $2M",
                "deductible": 5000.0,
                "included_endorsements": ["Basic Extended Coverage", "Vandalism"],
                "recommended": False
            },
            {
                "tier_name": "Preferred (Recommended)",
                "annual_premium": total_base_premium,
                "property_limit": round(tiv * 1.15, 2),
                "gl_limit": "$2M / $4M",
                "deductible": 2500.0,
                "included_endorsements": [
                    "Water Backup & Sump Overflow",
                    "Equipment Breakdown Coverage",
                    "Business Interruption 12-Month ALS"
                ],
                "recommended": True
            },
            {
                "tier_name": "Comprehensive",
                "annual_premium": round(total_base_premium * 1.22, 2),
                "property_limit": round(tiv * 1.30, 2),
                "gl_limit": "$5M Commercial Umbrella",
                "deductible": 10000.0,
                "included_endorsements": [
                    "Full Cyber Liability ($1M)",
                    "Earthquake & Flood Sublimit ($1M)",
                    "Ordinance & Law Coverage A, B, C",
                    "Equipment Breakdown Coverage"
                ],
                "recommended": False
            }
        ]

        # Calculate Decision Hash
        trace_summary = {
            "submission_id": submission_id,
            "rule_version": self.rule_version,
            "score": final_score,
            "tier": tier,
            "property_premium": property_premium,
            "gl_premium": gl_premium,
            "total_premium": total_base_premium,
            "steps": steps_log
        }
        decision_hash = hashlib.sha256(json.dumps(trace_summary, sort_keys=True).encode()).hexdigest()

        return {
            "submission_id": submission_id,
            "rule_set_version": self.rule_version,
            "underwriting_risk_score": final_score,
            "risk_tier": tier,
            "credits_applied": credits_applied,
            "penalties_applied": penalties_applied,
            "property_premium": property_premium,
            "gl_premium": gl_premium,
            "total_base_premium": total_base_premium,
            "quote_options": quote_options,
            "decision_trace": steps_log,
            "decision_hash": decision_hash
        }

