# 02. Subagent Roster, Roles & Multi-Agent Workflows

## Master Subagent Roster Overview

The underwriting process demands specialized domain competencies, rigorous risk segregation, and strict compliance barriers. The system organizes 13 subagents in a **Hub-and-Spoke** topology orchestrated by the `lead_underwriting_orchestrator`.

```
                                  +---------------------------------------+
                                  |     lead_underwriting_orchestrator    |
                                  | (FCoT Supervisor & Synthesis Engine)  |
                                  +-------------------+-------------------+
                                                      |
         +--------------------+-----------------------+-----------------------+--------------------+
         |                    |                       |                       |                    |
+--------v-------+   +--------v-------+      +--------v-------+      +--------v-------+   +--------v-------+
| 01. intake_    |   | 02. clearance_ |      | 03. appetite_  |      | 04. data_      |   | 05. exposure_  |
| doc_agent      |   | sanctions_agent|      | eligibility_   |      | enrichment_    |   | analysis_agent |
+----------------+   +----------------+      | agent          |      | agent          |   +----------------+
                                             +----------------+      +----------------+
         +--------------------+-----------------------+-----------------------+--------------------+
         |                    |                       |                       |                    |
+--------v-------+   +--------v-------+      +--------v-------+      +--------v-------+   +--------v-------+
| 06. loss_      |   | 07. symbolic_  |      | 08. quote_     |      | 09. grounding_ |   | 10. triage_    |
| history_agent  |   | rating_engine  |      | structuring_   |      | compliance_    |   | referral_agent |
|                |   | (ZERO-LLM)     |      | agent          |      | agent          |   +----------------+
+----------------+   +----------------+      +----------------+      +----------------+
                                                      |
                                     +----------------+----------------+
                                     |                                 |
                            +--------v-------+                +--------v-------+
                            | 11. quote_     |                | 12. audit_     |
                            | lifecycle_agent|                | governance_    |
                            |                |                | agent          |
                            +----------------+                +----------------+
```

---

## Detailed Subagent Specifications

### 1. `intake_doc_agent` (Intake & Document Ingestion Specialist)
* **Architectural Purpose**: Ingests multi-format insurance submission packages (ACORD 125, ACORD 126, ACORD 140, Statements of Values (SOVs), Loss Run reports, and financial schedules) from Google Cloud Storage. Invokes Document AI processors to extract structured key-value entities, tabular rows, and character-level bounding box spans.
* **Grounding Constraint**: Must attach character coordinates `(page, start_char, end_char, bbox)` to every extracted field. No ungrounded field may pass to downstream agents.
* **Authorized Tools**: `gcs_read_submission_package`, `docai_process_document_batch`, `store_extracted_spans_in_memory`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/intake-doc` (Read-only GCS, invoke Doc AI).
* **Input Schema**:
  ```python
  class IntakeRequest(BaseModel):
      submission_id: str
      gcs_bucket: str
      gcs_object_paths: List[str]
      timestamp: datetime
  ```
* **Output Schema**:
  ```python
  class ExtractedEntity(BaseModel):
      field_name: str
      field_value: Any
      confidence: float
      source_file: str
      page_number: int
      char_span: Tuple[int, int]
      bbox: List[float]
      span_hash: str

  class IntakeResult(BaseModel):
      submission_id: str
      applicant_name: str
      primary_address: str
      business_description: str
      lines_requested: List[str] # ["Commercial Property", "General Liability"]
      extracted_entities: List[ExtractedEntity]
      raw_table_data: Dict[str, List[Dict[str, Any]]]
  ```

---

### 2. `clearance_sanctions_agent` (Clearance & Identity Specialist)
* **Architectural Purpose**: Evaluates applicant against sanctions lists (OFAC SDN, Politically Exposed Persons (PEP), Consolidated Sanctions List), performs Customer Identification Program (CIP) validation, and checks internal portfolio databases for duplicate submissions or existing policy blocks.
* **Grounding Constraint**: Every clearance approval or hit must cite the exact OFAC database version timestamp, search hash, and matching score threshold.
* **Authorized Tools**: `ofac_sdn_lookup`, `cip_identity_verify`, `bigquery_duplicate_submission_check`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/clearance-sanctions` (Read-only sanctions DB, read-only BigQuery portfolio).
* **Input Schema**: `ClearanceRequest(applicant_name, dba_name, ein, address, principal_names)`
* **Output Schema**:
  ```python
  class ClearanceResult(BaseModel):
      submission_id: str
      ofac_status: Literal["CLEAR", "HIT", "POTENTIAL_MATCH"]
      ofac_match_score: float
      ofac_record_id: Optional[str]
      cip_status: Literal["VERIFIED", "UNVERIFIED", "SUSPICIOUS"]
      duplicate_status: Literal["NO_DUPLICATE", "EXISTING_ACCOUNT", "BROKER_CONFLICT"]
      clearance_approved: bool
      citation: Dict[str, str] # {"db": "OFAC_SDN_2026_08", "query_hash": "a1b2c3..."}
  ```

---

### 3. `appetite_eligibility_agent` (Underwriting Appetite Specialist)
* **Architectural Purpose**: Classifies the applicant's line of business into standardized NAICS/SIC codes, cross-referencing company underwriting appetite guidelines, restricted class lists, and state-specific licensing restrictions.
* **Grounding Constraint**: Must reference exact Appetite Guideline Rule IDs (e.g., `APP-RULE-PROP-2026-04`) and cite the extracted business description span.
* **Authorized Tools**: `naics_classifier_lookup`, `appetite_rules_engine_query`, `state_licensing_check`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/appetite-eligibility` (Read-only rules catalog).
* **Input Schema**: `AppetiteRequest(submission_id, business_description, proposed_operations, state)`
* **Output Schema**:
  ```python
  class AppetiteResult(BaseModel):
      submission_id: str
      naics_code: str
      sic_code: str
      class_description: str
      appetite_tier: Literal["PREFERRED", "STANDARD", "SPECIALTY_REFERRAL", "PROHIBITED"]
      eligible: bool
      appetite_rule_id: str
      justification: str
      grounded_span_ref: str
  ```

---

### 4. `data_enrichment_agent` (External Data & Hazard Specialist)
* **Architectural Purpose**: Queries external and geospatial data services (via Apigee API Gateway) to fetch parcel attributes, distance to coast, FEMA flood zone maps, wildfire hazard indices, ISO Public Protection Classification (PPC), building construction history, and Dun & Bradstreet / credit risk scores.
* **Grounding Constraint**: Every enriched data point must store the source API response payload SHA-256 hash and query endpoint URL.
* **Authorized Tools**: `apigee_hazard_zone_lookup`, `apigee_iso_ppc_lookup`, `apigee_financial_health_lookup`, `bigquery_historical_cat_lookup`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/data-enrichment` (Invoke Apigee data APIs, read-only BigQuery).
* **Input Schema**: `EnrichmentRequest(submission_id, location_addresses, entity_tin)`
* **Output Schema**:
  ```python
  class LocationEnrichment(BaseModel):
      address: str
      latitude: float
      longitude: float
      fema_flood_zone: str
      wildfire_risk_index: float # 1.0 to 10.0
      earthquake_zone: str
      iso_protection_class: int # 1 (best) to 10 (unprotected)
      distance_to_coast_miles: float
      distance_to_fire_station_miles: float
      commercial_credit_score: int
      payload_sha256: str

  class EnrichmentResult(BaseModel):
      submission_id: str
      locations: List[LocationEnrichment]
      financial_stability_index: float
      enrichment_timestamp: datetime
  ```

---

### 5. `exposure_analysis_agent` (COPE & Physical Risk Specialist)
* **Architectural Purpose**: Analyzes physical property risks using the classical **COPE** framework (**C**onstruction, **O**ccupancy, **P**rotection, **E**xposure). Evaluates Total Insured Value (TIV), Probable Maximum Loss (PML), and Maximum Foreseeable Loss (MFL).
* **Grounding Constraint**: Construction type (ISO 1-6), square footage, year built, and roof age must cite exact document spans or enrichment records.
* **Authorized Tools**: `calculate_cope_metrics`, `sov_aggregate_tiv`, `pml_mfl_estimator`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/exposure-analysis` (Read-only compute tools).
* **Input Schema**: `ExposureRequest(submission_id, locations, extracted_sov_rows, building_specs)`
* **Output Schema**:
  ```python
  class COPEProfile(BaseModel):
      location_id: str
      construction_type: Literal["Frame", "Joisted_Masonry", "Non_Combustible", "Masonry_Non_Combustible", "Modified_Fire_Resistive", "Fire_Resistive"]
      occupancy_hazard_grade: Literal["Low", "Medium", "High", "Severe"]
      protection_system: Literal["Full_Sprinkler_NFPA13", "Partial_Sprinkler", "Standpipe_Only", "Unsprinklered"]
      exposure_threat_level: Literal["Low", "Moderate", "High"]
      total_insured_value: float
      probable_maximum_loss_pct: float
      pml_dollar_amount: float
      evidence_citations: List[str]

  class ExposureResult(BaseModel):
      submission_id: str
      portfolio_tiv: float
      cope_profiles: List[COPEProfile]
      overall_exposure_tier: Literal["LOW_RISK", "MODERATE_RISK", "ELEVATED_RISK", "HIGH_RISK"]
  ```

---

### 6. `loss_history_agent` (Loss Run & Actuarial Claims Specialist)
* **Architectural Purpose**: Deconstructs 5-year historical loss runs, parsing loss dates, claim descriptions, amounts paid, outstanding reserves, and subrogation recoveries. Computes loss frequency, loss severity, historical loss ratios, and trended loss development factors.
* **Grounding Constraint**: Every past claim item must map back to a line item in the loss run PDF with verified monetary totals.
* **Authorized Tools**: `parse_loss_run_table`, `compute_loss_triangle_metrics`, `actuarial_trend_losses`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/loss-history` (Read-only actuarial calculators).
* **Input Schema**: `LossHistoryRequest(submission_id, loss_run_files, premium_history_by_year)`
* **Output Schema**:
  ```python
  class ClaimRecord(BaseModel):
      claim_id: str
      date_of_loss: str
      claim_type: str # "Water Damage", "Fire", "Slip & Fall"
      paid_amount: float
      reserved_amount: float
      status: Literal["OPEN", "CLOSED"]
      subrogation_recovery: float
      source_span_id: str

  class LossHistoryResult(BaseModel):
      submission_id: str
      five_year_total_incurred: float
      five_year_loss_ratio: float
      open_claim_count: int
      frequency_index: Literal["EXCELLENT_ZERO", "LOW_1_2", "MODERATE_3_5", "HIGH_GT_5"]
      severity_index: Literal["LOW_LT_25K", "MEDIUM_25K_100K", "HIGH_GT_100K"]
      experience_modifier_calc: float # e.g. 0.92 (credit) or 1.15 (debit)
      claims: List[ClaimRecord]
  ```

---

### 7. `symbolic_rating_engine` (Deterministic Actuarial Core — ZERO-LLM)
* **Architectural Purpose**: The purely deterministic symbolic calculation engine. Executes published ISO/actuarial rating algorithms, applying base rates, territory multipliers, construction factors, protection class credits, loss experience modifiers (E-Mod), and discretionary schedule credits/debits within statutory maximums ($\pm 25\%$).
* **STRICT HARD REQUIREMENT**: **ZERO LLM CALLS**. No neural models, embeddings, or stochastic samplers are permitted within this agent. Pure mathematical and logical evaluation in Python.
* **Determinism Invariant**: `f(Inputs, RuleVersion) -> (Scores, Rates, Premiums, DecisionTrace)`. Bitwise identical outputs on identical inputs.
* **Authorized Tools**: Pure mathematical library only (`math`, `decimal`). No network egress.
* **SPIFFE Role**: `spiffe://amtha.net/agent/symbolic-rating` (No network access, isolated memory compute).
* **Input Schema**: `SymbolicRatingInput(submission_id, tiv, cope_profiles, loss_history_result, enrichment_data, rule_set_version="v2026.3")`
* **Output Schema**:
  ```python
  class RateComponentBreakdown(BaseModel):
      base_rate_per_hundred: float
      territory_factor: float
      construction_factor: float
      protection_class_factor: float
      experience_modifier: float
      schedule_rating_credit_debit: float
      final_rate_per_hundred: float
      annual_technical_premium: float
      rule_step_ids: List[str]

  class SymbolicRatingResult(BaseModel):
      submission_id: str
      rule_set_version: str
      underwriting_risk_score: int # 0 to 100
      score_risk_tier: Literal["PREFERRED_STP", "STANDARD", "REFERRAL_REQUIRED", "DECLINE"]
      property_breakdown: RateComponentBreakdown
      liability_breakdown: RateComponentBreakdown
      total_annual_base_premium: float
      deterministic_decision_trace: List[Dict[str, Any]]
      computation_sha256: str
  ```

---

### 8. `quote_structuring_agent` (Quote Packages & Tiering Specialist)
* **Architectural Purpose**: Takes deterministic rating output and structures 3 commercial quote packages tailored for the broker:
  1. **Standard / Basic Option**: Standard limits ($1M Occurrence / $2M Aggregate, $5,000 deductible), essential property coverages.
  2. **Recommended / Preferred Option**: Optimized balance ($2M Occurrence / $4M Aggregate, $2,500 deductible, water backup endorsement, equipment breakdown, business interruption 12-month actual loss sustained).
  3. **High-Deductible / Comprehensive Option**: Higher limits ($5M Umbrella layer, $10,000 deductible, cyber liability endorsement, extended flood/earthquake sublimits).
* **Grounding Constraint**: All premiums across options must be calculated using the symbolic rating engine formulas.
* **Authorized Tools**: `generate_quote_schedules`, `apply_deductible_credits`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/quote-structuring` (Read-only rating output).
* **Input Schema**: `QuoteStructureRequest(submission_id, rating_result, policy_effective_date)`
* **Output Schema**:
  ```python
  class QuoteOption(BaseModel):
      option_id: str
      tier_name: Literal["Basic", "Preferred_Recommended", "Comprehensive"]
      annual_premium: float
      property_limit: float
      general_liability_limit: float
      deductible: float
      included_endorsements: List[str]
      monthly_payment_estimate: float
      subjectivities_and_conditions: List[str]
      pricing_rule_hash: str

  class QuoteStructureResult(BaseModel):
      submission_id: str
      quote_id: str
      quote_timestamp: datetime
      options: List[QuoteOption]
  ```

---

### 9. `grounding_compliance_agent` (Mechanical Grounding & Citation Guard)
* **Architectural Purpose**: The mechanical zero-hallucination compliance gate. Parses all natural-language text and summarized claims emitted by neural subagents. Extracts entity references, numerical metrics, dates, and addresses into an Abstract Syntax Tree (AST). Verifies that every single entity and claim has an active citation link to a source Doc AI span, enrichment API payload hash, or symbolic rule ID.
* **BLOCKING RULE**: If any claim cannot be resolved to a citation, the entire submission turn is **BLOCKED**. It never surfaces unverified text to underwriters or brokers.
* **Authorized Tools**: `ast_parse_claims`, `verify_span_registry`, `verify_rule_registry`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/grounding-compliance` (Internal memory validation).
* **Input Schema**: `GroundingVerificationRequest(submission_id, agent_outputs, citations_registry)`
* **Output Schema**:
  ```python
  class CitationVerification(BaseModel):
      claim_text: str
      entity_type: str # "TIV", "Address", "PriorLoss", "Score"
      claimed_value: Any
      citation_type: Literal["DOC_SPAN", "API_PAYLOAD_HASH", "SYMBOLIC_RULE_ID"]
      citation_target: str
      is_valid: bool
      verification_notes: str

  class GroundingVerificationResult(BaseModel):
      submission_id: str
      total_claims_checked: int
      passed_claims_count: int
      failed_claims_count: int
      is_grounded: bool # True if failed == 0
      blocked_reason: Optional[str]
      audit_grounding_certificate_id: str
  ```

---

### 10. `triage_referral_agent` (Triage & STP Decision Specialist)
* **Architectural Purpose**: Compares the symbolic risk score, appetite tier, compliance status, and exposure profile against company underwriting authority matrices. Deterministically routes the quote to **Straight-Through Processing (STP)** or creates an **Underwriter Referral Brief** with prioritized action items.
* **Routing Rules**:
  - **STP Approved**: Risk Score $\ge 85$, Appetite = `PREFERRED`, 0 Open Claims, 5-Yr Loss Ratio $< 20\%$, Flood Zone X/C, Clean OFAC/CIP.
  - **Referral Required**: Risk Score $60-84$, OR Loss Ratio $20\%-50\%$, OR TIV $> \$10\text{M}$, OR Wildfire Index $> 7.0$. Generates comprehensive Underwriter Referral Brief.
  - **Decline / Out of Appetite**: Risk Score $< 60$, OR Prohibited Class, OR OFAC Sanctions Hit.
* **Authorized Tools**: `authority_matrix_lookup`, `generate_referral_brief`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/triage-referral` (Read-only underwriting authority).
* **Input Schema**: `TriageRequest(submission_id, rating_result, appetite_result, cope_profile, loss_history)`
* **Output Schema**:
  ```python
  class ReferralBrief(BaseModel):
      referral_reasons: List[str]
      prioritized_risk_factors: List[str]
      recommended_underwriter_actions: List[str] # ["Request roof inspection report", "Increase property deductible to $10k"]
      recommended_conditions: List[str]

  class TriageResult(BaseModel):
      submission_id: str
      routing_decision: Literal["STRAIGHT_THROUGH_AUTO_QUOTE", "HUMAN_UNDERWRITER_REFERRAL", "AUTO_DECLINE"]
      underwriting_authority_level_required: Literal["AUTO", "UNDERWRITER_I", "SENIOR_UNDERWRITER_II", "CHIEF_UNDERWRITER"]
      referral_brief: Optional[ReferralBrief]
  ```

---

### 11. `quote_lifecycle_agent` (State Machine & Policy Administration)
* **Architectural Purpose**: Manages the complete, durable quote lifecycle state transitions. Guarantees that no quote is ever orphaned, fragmented, or lost across async sessions. Enforces state transition invariants (`DRAFT` $\to$ `INTAKE_COMPLETE` $\to$ `ENRICHED` $\to$ `RATED` $\to$ `QUOTED_STP` | `REFERRED` $\to$ `BOUND` | `DECLINED` | `EXPIRED`).
* **Grounding Constraint**: Every state change writes an immutable transaction event to BigQuery with cryptographic session nonces and UTC timestamps.
* **Authorized Tools**: `state_store_transition`, `quote_ttl_enforcer`, `bind_order_generator`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/quote-lifecycle` (Read/Write BigQuery Quote Ledger).
* **Input Schema**: `LifecycleTransitionRequest(quote_id, target_state, user_identity, payload_diff)`
* **Output Schema**:
  ```python
  class QuoteLifecycleState(BaseModel):
      quote_id: str
      submission_id: str
      current_state: Literal["DRAFT", "INGESTED", "ENRICHED", "RATED", "QUOTED_STP", "REFERRED", "UNDER_REVIEW", "BOUND", "DECLINED", "EXPIRED"]
      created_at: datetime
      updated_at: datetime
      expires_at: datetime
      is_orphaned: bool
      history_trail: List[Dict[str, Any]]
  ```

---

### 12. `audit_governance_agent` (Regulatory Audit & Compliance Pack Generator)
* **Architectural Purpose**: Assembles a regulator-ready audit pack for any quote or underwriting decision. Bundles raw intake document hashes, character span mappings, external enrichment receipts, actuarial rule versions, intermediate calculation logs, grounding verification certificates, and human underwriter override notes into an exportable, tamper-evident JSON/PDF package.
* **Grounding Constraint**: Generates a Merkle tree root hash of all inputs, outputs, and intermediate states.
* **Authorized Tools**: `generate_merkle_root`, `export_regulator_audit_bundle`, `publish_looker_audit_metrics`.
* **SPIFFE Role**: `spiffe://amtha.net/agent/audit-governance` (Read all session logs, write audit bundles).
* **Input Schema**: `AuditPackRequest(quote_id, submission_id)`
* **Output Schema**:
  ```python
  class AuditPackResult(BaseModel):
      audit_pack_id: str
      quote_id: str
      merkle_root_hash: str
      export_url_gcs: str
      decision_replay_verified: bool
      generated_at: datetime
      regulatory_compliance_checklist: Dict[str, bool] # {"ECOA_Compliant": True, "FCRA_Disclosed": True}
  ```

---

### 13. `lead_underwriting_orchestrator` (FCoT Supervisor Orchestrator)
* **Architectural Purpose**: Master coordinator implementing the **Fractal Chain of Thought (FCoT)** paradigm across Macro, Meso, and Micro analytical apertures. Executes the sequential dispatch loop, prevents subagent cross-talk, manages the shared epistemic context, hillclimbs subagent outputs, and streams real-time JSON-RPC telemetry frames and dynamic A2UI schema components to the frontend.
* **Execution Protocol**:
  1. Inspects session state flags (`intake_done`, `clearance_done`, `appetite_done`, `enrichment_done`, `exposure_done`, `loss_done`, `rating_done`, `quote_done`, `grounding_done`, `triage_done`, `lifecycle_done`, `audit_done`).
  2. Issues silent transfers (`transfer_to_agent(name="...")`) sequentially.
  3. When all 12 specialist modules complete, executes multi-scale synthesis and emits final A2UI `Tabs`, `Table`, `Card`, `RiskFactorBreakdown`, and `QuoteSelector` widgets over SSE.

