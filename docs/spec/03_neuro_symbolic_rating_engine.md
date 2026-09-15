# 03. Symbolic Rating Engine (Zero-LLM Actuarial Core)

## System Mission & The Zero-LLM Invariant

The **Symbolic Rating Engine** is the deterministic calculation backbone of the platform. Under insurance statutory regulations (e.g., NAIC Model Rating Laws, state Department of Insurance filings, FCRA), rating algorithms, risk scores, debits, credits, and quote premiums must be **explainable, auditable, and 100% reproducible**.

### The Zero-LLM Invariant
```
+-----------------------------------------------------------------------------+
|                          THE ZERO-LLM INVARIANT                             |
|                                                                             |
|  1. Under NO circumstances may an LLM generate a numerical rate, premium,   |
|     debit/credit multiplier, risk score, or automated bind/decline decision.|
|  2. Zero stochastic functions, zero temperature samplers, zero random seeds.|
|  3. Pure functional programming:                                            |
|     f(Inputs, RuleVersion) -> (RiskScore, TechnicalPremium, DecisionTrace)  |
|  4. Invariant: Same Inputs + Same RuleVersion === Identical Decision Trace. |
+-----------------------------------------------------------------------------+
```

---

## Mathematical Specification & Rating Formulas

### 1. Actuarial Technical Premium Formulation (Commercial Property)

For a commercial property submission with Total Insured Value ($TIV$), the annual technical property premium $P_{\text{property}}$ is formulated as:

$$P_{\text{property}} = \left( \frac{TIV}{100} \right) \times R_{\text{base}} \times F_{\text{terr}} \times F_{\text{const}} \times F_{\text{occ}} \times F_{\text{prot}} \times F_{\text{cat}} \times E_{\text{mod}} \times (1 + C_{\text{sched}})$$

Where:
* $TIV$: Total Insured Value (Building + Business Personal Property + Business Interruption) in USD.
* $R_{\text{base}}$: Base rate per $\$100$ of value, determined by NAICS / ISO Class Code.
* $F_{\text{terr}}$: Territory multiplier indexed by postal code / county.
* $F_{\text{const}}$: Construction multiplier (ISO Construction Classes 1 through 6).
* $F_{\text{occ}}$: Occupancy hazard index multiplier.
* $F_{\text{prot}}$: ISO Public Protection Classification (PPC) factor (Grades 1 to 10).
* $F_{\text{cat}}$: Catastrophe loading factor ($F_{\text{cat}} = F_{\text{flood}} \times F_{\text{wildfire}} \times F_{\text{earthquake}}$).
* $E_{\text{mod}}$: Experience Rating Modifier computed from 5-year historical loss data.
* $C_{\text{sched}}$: Schedule rating credit/debit adjustment (Statutory constraint: $-0.25 \le C_{\text{sched}} \le +0.25$).

---

### 2. General Liability (GL) Premium Formulation

For commercial general liability covering premises and operations:

$$P_{\text{gl}} = \left( \frac{\text{Gross Revenue}}{1,000} \right) \times R_{\text{gl\_base}} \times F_{\text{terr}} \times F_{\text{limit\_relativity}} \times E_{\text{mod}} \times (1 + C_{\text{sched}})$$

---

### 3. Factor Lookup Matrices (RuleSet Version `v2026.3`)

#### A. ISO Construction Multipliers ($F_{\text{const}}$)
| ISO Class | Description | Frame / Material | $F_{\text{const}}$ |
|---|---|---|---|
| Class 1 | Frame | Wood / Combustible | $1.45$ |
| Class 2 | Joisted Masonry | Concrete/Brick walls, Wood roof | $1.20$ |
| Class 3 | Non-Combustible | Metal frame, Metal walls/roof | $1.00$ (Baseline) |
| Class 4 | Masonry Non-Combustible | Concrete/Block walls, Metal roof | $0.85$ |
| Class 5 | Modified Fire Resistive | Heavy concrete / Fire-protected steel | $0.70$ |
| Class 6 | Fire Resistive | Solid reinforced concrete structures | $0.55$ |

#### B. ISO Public Protection Class Multipliers ($F_{\text{prot}}$)
| ISO PPC Grade | Fire Hydrant / Station Proximity | $F_{\text{prot}}$ |
|---|---|---|
| Grade 1 - 2 | Exemplary protection ($< 1,000$ ft hydrant, $< 1.5$ mi station) | $0.85$ |
| Grade 3 - 4 | Standard urban/suburban municipal department | $0.95$ |
| Grade 5 - 6 | Moderate protection (Suburban/Rural with water tenders) | $1.10$ |
| Grade 7 - 8 | Limited protection ($> 1,000$ ft hydrant) | $1.30$ |
| Grade 9 - 10 | Unprotected / Remote volunteer fire department | $1.65$ |

#### C. Catastrophe & Hazard Loadings ($F_{\text{cat}}$)
| Hazard Factor | Metric Value | Factor Value | Rule ID |
|---|---|---|---|
| **FEMA Flood Zone** | Zone X / C (Minimal risk) | $1.00$ | `RULE-CAT-FLD-01` |
| | Zone AE / A (100-Year Special Hazard) | $1.45$ | `RULE-CAT-FLD-02` |
| | Zone V / VE (Coastal high velocity wave action) | $2.20$ (Requires referral) | `RULE-CAT-FLD-03` |
| **Wildfire Risk Index** | Index $1.0 - 3.0$ (Low) | $1.00$ | `RULE-CAT-WFR-01` |
| | Index $3.1 - 6.0$ (Moderate) | $1.15$ | `RULE-CAT-WFR-02` |
| | Index $6.1 - 8.5$ (Elevated) | $1.50$ | `RULE-CAT-WFR-03` |
| | Index $> 8.5$ (Severe) | $2.10$ (Requires referral) | `RULE-CAT-WFR-04` |

---

### 4. Experience Rating Modifier ($E_{\text{mod}}$) Formulation

Calculated deterministically from 5-year historical loss runs:

$$E_{\text{mod}} = 1.0 + \frac{A_{\text{losses}} - E_{\text{losses}}}{E_{\text{losses}} + K}$$

Where:
* $A_{\text{losses}}$: Actual trended 5-year incurred losses (Paid + Open Reserves - Subrogation).
* $E_{\text{losses}}$: Expected losses based on payroll/TIV exposure ($E_{\text{losses}} = TIV \times \text{Expected Loss Rate}$).
* $K$: Actuarial ballast constant to stabilize small accounts ($K = 50,000$).
* **Cap Constraints**: $0.70 \le E_{\text{mod}} \le 1.40$.

---

### 5. Deterministic Underwriting Risk Score ($0 - 100$)

The holistic risk score is evaluated as an additive/subtractive deterministic point model:

$$\text{Score} = \text{Clamp}_{[0, 100]} \left( 100 - \sum \text{Penalties} + \sum \text{Credits} \right)$$

```
Base Starting Points: 100

Deductions (Penalties):
- Construction:
  * ISO Class 1 (Frame): -12 pts
  * ISO Class 2 (Joisted Masonry): -6 pts
- Protection Class:
  * ISO PPC 7-8: -10 pts
  * ISO PPC 9-10: -20 pts
- Roof Age:
  * Roof Age 15-20 years: -8 pts
  * Roof Age > 20 years: -15 pts
- Hazard Zones:
  * Flood Zone AE: -15 pts
  * Wildfire Index > 6.0: -15 pts
- Loss History:
  * 1 Prior Loss (< $25k): -4 pts
  * 2-3 Prior Losses (< $100k): -12 pts
  * > 3 Prior Losses OR Single Loss > $100k: -25 pts
  * Open Active Claim: -15 pts

Additions (Credits):
- Fire Suppression:
  * Full NFPA 13 Sprinklers across 100% floor area: +10 pts
  * Central Station Fire & Burglar Alarm: +5 pts
- Loss Free Track:
  * 5 Consecutive Loss-Free Years: +8 pts
- Building Age / Modernization:
  * Full electrical/plumbing update in past 10 years: +5 pts
```

#### Score Risk Tiers:
* **$\text{Score} \ge 85$**: `PREFERRED_STP` (Eligible for automated straight-through quote).
* **$70 \le \text{Score} < 85$**: `STANDARD` (Eligible for automated quote with standard subjectivities).
* **$60 \le \text{Score} < 70$**: `REFERRAL_REQUIRED` (Must route to human underwriter with generated brief).
* **$\text{Score} < 60$**: `DECLINE` (Automatic decline recommendation).

---

## Decision Trace Schema & Proof of Determinism

Every rating evaluation generates an immutable JSON **Decision Trace** containing every formula, intermediate variable, and active rule ID:

```json
{
  "submission_id": "SUB-2026-90412",
  "rule_set_version": "v2026.3",
  "timestamp_utc": "2026-09-01T00:00:00Z",
  "input_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "steps": [
    {
      "step_index": 1,
      "step_name": "BaseRateLookup",
      "rule_id": "RULE-PROP-BASE-541512",
      "variables": {"naics": "541512", "class_code": "0074"},
      "result": {"base_rate_per_hundred": 0.28}
    },
    {
      "step_index": 2,
      "step_name": "ConstructionFactor",
      "rule_id": "RULE-CONST-CLASS-4",
      "variables": {"iso_construction_class": 4, "description": "Masonry Non-Combustible"},
      "result": {"factor": 0.85}
    },
    {
      "step_index": 3,
      "step_name": "ProtectionClassFactor",
      "rule_id": "RULE-PPC-GRADE-3",
      "variables": {"ppc_grade": 3},
      "result": {"factor": 0.95}
    },
    {
      "step_index": 4,
      "step_name": "ExperienceModifier",
      "rule_id": "RULE-EMOD-CALC-5YR",
      "variables": {"actual_losses": 12400.0, "expected_losses": 28000.0, "ballast_k": 50000.0},
      "result": {"emod": 0.80}
    },
    {
      "step_index": 5,
      "step_name": "TechnicalPremiumCalculation",
      "rule_id": "RULE-PREM-PROP-FINAL",
      "formula": "(TIV / 100) * base_rate * f_terr * f_const * f_occ * f_prot * f_cat * emod * (1 + c_sched)",
      "variables": {
        "tiv": 12500000.0,
        "base_rate": 0.28,
        "f_terr": 1.05,
        "f_const": 0.85,
        "f_occ": 1.00,
        "f_prot": 0.95,
        "f_cat": 1.00,
        "emod": 0.80,
        "c_sched": -0.05
      },
      "result": {"final_annual_property_premium": 22444.62}
    },
    {
      "step_index": 6,
      "step_name": "UnderwritingScoreEvaluation",
      "rule_id": "RULE-SCORE-PROP-2026",
      "variables": {
        "base_score": 100,
        "penalties": 0,
        "credits": [
          {"reason": "NFPA 13 Sprinklers", "points": 10},
          {"reason": "5-Yr Loss Free Track", "points": 8},
          {"reason": "Building Update < 10 Yrs", "points": 5}
        ]
      },
      "result": {"score": 89, "tier": "PREFERRED_STP"}
    }
  ],
  "final_outputs": {
    "risk_score": 89,
    "tier": "PREFERRED_STP",
    "annual_property_premium": 22444.62,
    "annual_gl_premium": 6850.00,
    "total_package_premium": 29294.62
  },
  "decision_hash": "c8f2b1d37a892e6e3441a108422409f8742845c4793540c11f42e4726ef3521d"
}
```

---

## Unit Testing & Bitwise Reproducibility Verification
Automated pytest suites test:
1. **Mathematical Invariance**: 10,000 simulated input permutations executed twice yield `100.0%` bitwise identical JSON traces.
2. **Boundary Checks**: Verification that $C_{\text{sched}}$ never exceeds $\pm 0.25$ and $E_{\text{mod}}$ never exceeds $[0.70, 1.40]$.
3. **No External Network Calls**: Sandboxed execution unit test verifies that `SymbolicRatingEngine` performs zero socket binds, HTTP requests, or imports of LLM/neural packages.

