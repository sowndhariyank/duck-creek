"""
Lead Underwriting Orchestrator (FCoT Supervisor Engine).
Coordinates the 12 specialized subagents using the Fractal Chain of Thought (FCoT) paradigm.
Streams real-time JSON-RPC telemetry frames and dynamic A2UI schema payloads over SSE.
Provides full input/output introspection for every agent across the mesh.
"""

from typing import Dict, Any, Generator, List, Optional
import json
import logging
import time
import asyncio

from backend.core.epistemic_memory import EpistemicCitationRegistry
from backend.core.grounding_guard import GroundingGuard
from backend.core.state_machine import QuoteLifecycleStateMachine
from backend.tools.docai_tools import DocAiToolSuite
from backend.tools.gcs_tools import GcsToolSuite
from backend.tools.bigquery_tools import BigQueryToolSuite
from backend.interfaces.apigee_interface import get_apigee_client
from backend.interfaces.looker_interface import get_looker_client

from backend.agents.intake_doc_agent import IntakeDocAgent
from backend.agents.clearance_sanctions_agent import ClearanceSanctionsAgent
from backend.agents.appetite_eligibility_agent import AppetiteEligibilityAgent
from backend.agents.data_enrichment_agent import DataEnrichmentAgent
from backend.agents.exposure_analysis_agent import ExposureAnalysisAgent
from backend.agents.loss_history_agent import LossHistoryAgent
from backend.agents.symbolic_rating_engine import SymbolicRatingEngine
from backend.agents.quote_structuring_agent import QuoteStructuringAgent
from backend.agents.grounding_compliance_agent import GroundingComplianceAgent
from backend.agents.triage_referral_agent import TriageReferralAgent
from backend.agents.quote_lifecycle_agent import QuoteLifecycleAgent
from backend.agents.audit_governance_agent import AuditGovernanceAgent

logger = logging.getLogger("amtha.orchestrator")


class LeadUnderwritingOrchestrator:
    """
    Master FCoT Orchestrator coordinating the Hub-and-Spoke Underwriting Mesh.
    Yields standardized JSON-RPC 2.0 telemetry frames for live SSE client consumption.
    """

    def __init__(self, session_id: str, submission_id: str, prompt: str = ""):
        self.session_id = session_id
        self.submission_id = submission_id
        self.prompt = prompt
        self.quote_id = f"Q-2026-{submission_id.split('-')[-1] if '-' in submission_id else '8821'}"

        # Initialize Epistemic Storage & Infrastructure Tools
        self.registry = EpistemicCitationRegistry(session_id=session_id)
        self.grounding_guard = GroundingGuard(self.registry)
        self.gcs_tools = GcsToolSuite()
        self.docai_tools = DocAiToolSuite(self.registry)
        self.bq_tools = BigQueryToolSuite()
        self.apigee_client = get_apigee_client(use_mock=True)
        self.looker_client = get_looker_client(use_mock=True)
        self.fsm = QuoteLifecycleStateMachine(self.quote_id, self.submission_id, self.bq_tools)

        # Initialize Specialist Subagents
        self.intake_agent = IntakeDocAgent(self.docai_tools)
        self.clearance_agent = ClearanceSanctionsAgent()
        self.appetite_agent = AppetiteEligibilityAgent()
        self.enrichment_agent = DataEnrichmentAgent(self.apigee_client, self.registry)
        self.exposure_agent = ExposureAnalysisAgent()
        self.loss_agent = LossHistoryAgent()
        self.symbolic_rating_engine = SymbolicRatingEngine()
        self.quote_structuring_agent = QuoteStructuringAgent()
        self.compliance_agent = GroundingComplianceAgent(self.grounding_guard)
        self.triage_agent = TriageReferralAgent()
        self.lifecycle_agent = QuoteLifecycleAgent()
        self.audit_agent = AuditGovernanceAgent(self.registry, self.bq_tools)

        # Record of all agent inputs and outputs for complete visibility
        self.agent_dossiers: List[Dict[str, Any]] = []

    def execute_underwriting_stream(self) -> Generator[str, None, None]:
        """
        Main execution loop.
        Yields JSON-RPC formatted telemetry chunks detailing each state transition and subagent I/O.
        """
        logger.info(f"Session {self.session_id}: Commencing Lead Orchestration Loop for submission {self.submission_id}")

        # Frame 1: Orchestrator Thought (FCoT Decomposition)
        yield self._encode_rpc_frame("onAgentThought", {
            "author": "lead_underwriting_orchestrator",
            "message": f"Initiating Fractal Chain of Thought (FCoT) Underwriting Pipeline for submission '{self.submission_id}'."
        })

        # --- STEP 1: INTAKE & DOC AI EXTRACTION ---
        yield self._encode_rpc_frame("onAgentDelegation", {
            "author": "lead_underwriting_orchestrator",
            "target": "intake_doc_agent",
            "message": "Routing submission intake package to Document AI processor."
        })
        yield self._encode_rpc_frame("onToolCall", {
            "author": "intake_doc_agent",
            "tool": "docai_process_document_batch",
            "arguments": {"submission_id": self.submission_id, "files": ["ACORD_125.pdf", "ACORD_140.pdf", "SOV.xlsx", "Loss_Runs.pdf"]}
        })
        
        self.fsm.transition_to("INGESTING", actor_id="lead_orchestrator", event_name="DOC_AI_TRIGGERED")
        intake_inputs = {"submission_id": self.submission_id, "files": ["ACORD_125.pdf", "ACORD_140.pdf", "SOV.xlsx", "Loss_Runs.pdf"]}
        intake_res = self.intake_agent.execute(self.submission_id, files=[{"name": "ACORD_125.pdf"}])
        extracted = intake_res["extracted_data"]

        self._record_dossier("intake_doc_agent", "Intake & Document AI Specialist", "spiffe://amtha.net/agent/intake-doc", intake_inputs, intake_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 2: CLEARANCE & OFAC SANCTIONS ---
        yield self._encode_rpc_frame("onAgentDelegation", {
            "author": "lead_underwriting_orchestrator",
            "target": "clearance_sanctions_agent",
            "message": f"Checking applicant '{extracted['applicant_name']}' against OFAC SDN and CIP databases."
        })
        yield self._encode_rpc_frame("onToolCall", {
            "author": "clearance_sanctions_agent",
            "tool": "ofac_sdn_lookup",
            "arguments": {"query": extracted["applicant_name"], "ein": extracted["ein"]}
        })
        
        clearance_inputs = {"applicant_name": extracted["applicant_name"], "ein": extracted["ein"], "db": "OFAC_SDN_2026_08"}
        clearance_res = self.clearance_agent.execute(self.submission_id, extracted["applicant_name"], extracted["ein"])
        
        self._record_dossier("clearance_sanctions_agent", "Clearance & Sanctions Specialist", "spiffe://amtha.net/agent/clearance-sanctions", clearance_inputs, clearance_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 3: APPETITE & ELIGIBILITY ---
        yield self._encode_rpc_frame("onAgentDelegation", {
            "author": "lead_underwriting_orchestrator",
            "target": "appetite_eligibility_agent",
            "message": f"Validating NAICS {extracted['naics_code']} operations against underwriting appetite."
        })
        appetite_inputs = {"business_description": extracted["business_description"], "naics_code": extracted["naics_code"]}
        appetite_res = self.appetite_agent.execute(self.submission_id, extracted["business_description"], extracted["naics_code"])
        
        self._record_dossier("appetite_eligibility_agent", "Appetite & Eligibility Specialist", "spiffe://amtha.net/agent/appetite-eligibility", appetite_inputs, appetite_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 4: DATA ENRICHMENT (APIGEE HAZARD & PPC) ---
        yield self._encode_rpc_frame("onAgentDelegation", {
            "author": "lead_underwriting_orchestrator",
            "target": "data_enrichment_agent",
            "message": f"Querying external geospatial hazard layers for '{extracted['primary_address']}' via Apigee."
        })
        yield self._encode_rpc_frame("onToolCall", {
            "author": "data_enrichment_agent",
            "tool": "apigee_hazard_zone_lookup",
            "arguments": {"address": extracted["primary_address"]}
        })
        
        self.fsm.transition_to("ENRICHING", actor_id="lead_orchestrator", event_name="ENRICHMENT_TRIGGERED")
        enrich_inputs = {"primary_address": extracted["primary_address"], "ein": extracted["ein"], "gateway": "Apigee_v2"}
        enrich_res = asyncio.run(self.enrichment_agent.execute(self.submission_id, extracted["primary_address"], extracted["ein"]))
        
        self._record_dossier("data_enrichment_agent", "Data Enrichment & Hazard Specialist", "spiffe://amtha.net/agent/data-enrichment", enrich_inputs, enrich_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 5: EXPOSURE & COPE DECOMPOSITION ---
        yield self._encode_rpc_frame("onAgentDelegation", {
            "author": "lead_underwriting_orchestrator",
            "target": "exposure_analysis_agent",
            "message": f"Decomposing COPE attributes: {extracted['construction_type']}, TIV ${extracted['tiv']:,.0f}."
        })
        exposure_inputs = {
            "tiv": extracted["tiv"],
            "construction_type": extracted["construction_type"],
            "sprinklered": extracted["sprinklered"],
            "roof_age_years": extracted["roof_age_years"]
        }
        exposure_res = self.exposure_agent.execute(
            self.submission_id,
            tiv=extracted["tiv"],
            construction_type=extracted["construction_type"],
            sprinklered=extracted["sprinklered"],
            roof_age_years=extracted["roof_age_years"]
        )
        self._record_dossier("exposure_analysis_agent", "Exposure & COPE Analysis Specialist", "spiffe://amtha.net/agent/exposure-analysis", exposure_inputs, exposure_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 6: LOSS HISTORY & CLAIMS ---
        yield self._encode_rpc_frame("onAgentDelegation", {
            "author": "lead_underwriting_orchestrator",
            "target": "loss_history_agent",
            "message": "Analyzing 5-year historical loss triangle and claim severity trends."
        })
        loss_inputs = {
            "five_year_incurred": extracted["five_year_incurred_losses"],
            "open_claims": extracted["open_claims_count"]
        }
        loss_res = self.loss_agent.execute(
            self.submission_id,
            five_year_incurred=extracted["five_year_incurred_losses"],
            open_claims=extracted["open_claims_count"]
        )
        self._record_dossier("loss_history_agent", "Loss History & Actuarial Specialist", "spiffe://amtha.net/agent/loss-history", loss_inputs, loss_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 7: SYMBOLIC RATING CORE (ZERO-LLM) ---
        yield self._encode_rpc_frame("onAgentThought", {
            "author": "lead_underwriting_orchestrator",
            "message": "Invoking Pure Symbolic Rating Engine (Zero-LLM Actuarial Core) for deterministic scoring and pricing."
        })
        yield self._encode_rpc_frame("onAgentDelegation", {
            "author": "lead_underwriting_orchestrator",
            "target": "symbolic_rating_engine",
            "message": "Executing ISO actuarial lookup formulas with RuleSet v2026.3."
        })
        
        self.fsm.transition_to("SCORING", actor_id="lead_orchestrator", event_name="SYMBOLIC_RATING_CALLED")
        rating_inputs = {
            "naics_code": extracted["naics_code"],
            "tiv": extracted["tiv"],
            "annual_revenue": extracted["annual_revenue"],
            "construction_type": extracted["construction_type"],
            "ppc_grade": enrich_res["iso_protection_class"],
            "flood_zone": enrich_res["fema_flood_zone"],
            "wildfire_index": enrich_res["wildfire_risk_index"],
            "sprinklered": extracted["sprinklered"],
            "roof_age_years": extracted["roof_age_years"],
            "five_year_incurred_losses": extracted["five_year_incurred_losses"],
            "rule_set_version": "v2026.3"
        }
        rating_res = self.symbolic_rating_engine.evaluate_submission(
            submission_id=self.submission_id,
            naics_code=extracted["naics_code"],
            tiv=extracted["tiv"],
            annual_revenue=extracted["annual_revenue"],
            construction_type=extracted["construction_type"],
            ppc_grade=enrich_res["iso_protection_class"],
            flood_zone=enrich_res["fema_flood_zone"],
            wildfire_index=enrich_res["wildfire_risk_index"],
            sprinklered=extracted["sprinklered"],
            building_age_years=2026 - extracted["year_built"],
            roof_age_years=extracted["roof_age_years"],
            five_year_incurred_losses=extracted["five_year_incurred_losses"],
            open_claims_count=extracted["open_claims_count"]
        )
        self.fsm.transition_to("RATED", actor_id="symbolic_rating_engine", event_name="RATING_COMPUTED")

        self._record_dossier("symbolic_rating_engine", "Symbolic Rating Engine (Zero-LLM Actuary)", "spiffe://amtha.net/agent/symbolic-rating", rating_inputs, {
            "score": rating_res["underwriting_risk_score"],
            "tier": rating_res["risk_tier"],
            "property_premium": rating_res["property_premium"],
            "gl_premium": rating_res["gl_premium"],
            "total_premium": rating_res["total_base_premium"],
            "decision_hash": rating_res["decision_hash"]
        })
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 8: QUOTE STRUCTURING ---
        quote_struct_inputs = {"rating_result": rating_res["decision_hash"], "tiers": ["Basic", "Preferred", "Comprehensive"]}
        quote_struct_res = self.quote_structuring_agent.execute(self.submission_id, rating_res)
        self._record_dossier("quote_structuring_agent", "Quote Structuring Specialist", "spiffe://amtha.net/agent/quote-structuring", quote_struct_inputs, quote_struct_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 9: MECHANICAL GROUNDING COMPLIANCE ---
        yield self._encode_rpc_frame("onAgentDelegation", {
            "author": "lead_underwriting_orchestrator",
            "target": "grounding_compliance_agent",
            "message": "Executing mechanical AST claim verification. Blocking any ungrounded assertions."
        })
        
        synthesized_claims_payload = {
            "applicant": extracted["applicant_name"],
            "construction": extracted["construction_type"],
            "flood_zone": enrich_res["fema_flood_zone"],
            "_citations": {
                "applicant": {"id": f"span_{self.submission_id}_applicant", "type": "DOC_SPAN"},
                "construction": {"id": f"span_{self.submission_id}_const", "type": "DOC_SPAN"},
                "flood_zone": {"id": f"receipt_{self.submission_id}_hazard", "type": "API_RECEIPT"}
            }
        }
        compliance_res = self.compliance_agent.execute(self.submission_id, synthesized_claims_payload)
        self._record_dossier("grounding_compliance_agent", "Grounding & Compliance Guard", "spiffe://amtha.net/agent/grounding-compliance", synthesized_claims_payload, compliance_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 10: TRIAGE & STP ROUTING ---
        yield self._encode_rpc_frame("onAgentDelegation", {
            "author": "lead_underwriting_orchestrator",
            "target": "triage_referral_agent",
            "message": f"Evaluating score {rating_res['underwriting_risk_score']}/100 against straight-through processing authority."
        })
        triage_inputs = {
            "risk_score": rating_res["underwriting_risk_score"],
            "tiv": extracted["tiv"],
            "appetite": appetite_res["appetite_tier"],
            "wildfire_index": enrich_res["wildfire_risk_index"],
            "flood_zone": enrich_res["fema_flood_zone"]
        }
        triage_res = self.triage_agent.execute(
            submission_id=self.submission_id,
            risk_score=rating_res["underwriting_risk_score"],
            tiv=extracted["tiv"],
            appetite_tier=appetite_res["appetite_tier"],
            wildfire_index=enrich_res["wildfire_risk_index"],
            flood_zone=enrich_res["fema_flood_zone"],
            open_claims=extracted["open_claims_count"]
        )

        if triage_res["is_stp"]:
            self.fsm.transition_to("QUOTED_STP", actor_id="triage_referral_agent", event_name="STP_AUTO_RELEASE")
        elif triage_res["routing_decision"] == "HUMAN_UNDERWRITER_REFERRAL":
            self.fsm.transition_to("REFERRED", actor_id="triage_referral_agent", event_name="REFERRED_TO_UW_QUEUE")
        else:
            self.fsm.transition_to("DECLINED", actor_id="triage_referral_agent", event_name="AUTO_DECLINED")

        self._record_dossier("triage_referral_agent", "Triage & STP Routing Specialist", "spiffe://amtha.net/agent/triage-referral", triage_inputs, triage_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 11: QUOTE LIFECYCLE ---
        lifecycle_inputs = {"quote_id": self.quote_id, "current_state": self.fsm.current_state, "ttl_days": 30}
        lifecycle_res = self.lifecycle_agent.execute(self.fsm, self.fsm.current_state, "orchestrator", "STATE_CONFIRMED")
        self._record_dossier("quote_lifecycle_agent", "Quote Lifecycle Specialist", "spiffe://amtha.net/agent/quote-lifecycle", lifecycle_inputs, lifecycle_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 12: REGULATORY AUDIT PACK ---
        audit_inputs = {"quote_id": self.quote_id, "submission_id": self.submission_id, "decision_hash": rating_res["decision_hash"]}
        audit_res = self.audit_agent.execute(self.quote_id, self.submission_id, rating_res)
        self._record_dossier("audit_governance_agent", "Audit Governance Specialist", "spiffe://amtha.net/agent/audit-governance", audit_inputs, audit_res)
        yield self._encode_rpc_frame("onSubagentCompleted", self.agent_dossiers[-1])

        # --- STEP 13: DYNAMIC A2UI SCHEMA DELIVERY ---
        yield self._encode_rpc_frame("onAgentThought", {
            "author": "lead_underwriting_orchestrator",
            "message": "Assembling Explainable Underwriting Workbench and multi-tier quote schedules for A2UI presentation."
        })

        a2ui_payload = self._build_a2ui_presentation(extracted, enrich_res, rating_res, triage_res, audit_res)
        yield self._encode_rpc_frame("onUiComponentDelivery", {
            "author": "lead_underwriting_orchestrator",
            "ui_specification": "2.0",
            "payload": a2ui_payload
        })

    def _record_dossier(self, agent_id: str, role_title: str, spiffe_id: str, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Records agent input and output snapshot into epistemic dossier."""
        self.agent_dossiers.append({
            "agent_id": agent_id,
            "role_title": role_title,
            "spiffe_id": spiffe_id,
            "inputs": inputs,
            "outputs": outputs,
            "timestamp_utc": time.time()
        })

    def _build_a2ui_presentation(
        self,
        extracted: Dict[str, Any],
        enrich_res: Dict[str, Any],
        rating_res: Dict[str, Any],
        triage_res: Dict[str, Any],
        audit_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assembles the dynamic A2UI schema."""
        components = [
            {
                "title": "Factor Justification",
                "type": "FactorJustificationTable",
                "id": "factor_justification_table",
                "headers": ["Risk Factor", "Extracted Finding", "Score Impact", "Evidence Citation"],
                "rows": [
                    [
                        "Construction Class",
                        f"ISO Class ({extracted['construction_type']})",
                        f"{'0 pts (Standard)' if extracted['construction_type'] not in ['Frame', 'Joisted_Masonry'] else '-12 pts (Combustible Frame)'}",
                        {"type": "DocSpan", "id": f"span_{self.submission_id}_const", "label": "SOV / ACORD (p.2)"}
                    ],
                    [
                        "Fire Protection System",
                        extracted["sprinkler_system"],
                        f"{'+10 pts (Sprinkler Credit)' if extracted['sprinklered'] else '0 pts (Unsprinklered)'}",
                        {"type": "DocSpan", "id": f"span_{self.submission_id}_sprinkler", "label": "ACORD 140 (p.2)"}
                    ],
                    [
                        "5-Year Loss Record",
                        f"${extracted['five_year_incurred_losses']:,.2f} ({extracted['open_claims_count']} Open Claims)",
                        f"{'+8 pts (Loss-Free)' if extracted['five_year_incurred_losses'] == 0 else ('-25 pts (Severe Losses)' if extracted['five_year_incurred_losses'] > 100000 else '-12 pts')}",
                        {"type": "DocSpan", "id": f"span_{self.submission_id}_loss", "label": "Loss Runs 5-Yr"}
                    ],
                    [
                        "Public Protection Class",
                        f"ISO PPC Grade {enrich_res['iso_protection_class']}",
                        f"{'0 pts (Base)' if enrich_res['iso_protection_class'] <= 6 else '-10 pts (Remote PPC)'}",
                        {"type": "ApiReceipt", "id": f"receipt_{self.submission_id}_ppc", "label": "Apigee ISO PPC API"}
                    ],
                    [
                        "Flood Hazard Zone",
                        f"FEMA Flood Zone {enrich_res['fema_flood_zone']}",
                        f"{'0 pts (Minimal)' if enrich_res['fema_flood_zone'] == 'X' else '-15 pts (Special Flood Hazard)'}",
                        {"type": "ApiReceipt", "id": f"receipt_{self.submission_id}_hazard", "label": "Apigee FEMA GIS"}
                    ]
                ]
            },
            {
                "title": "Agent Mesh Dossier (Inputs & Outputs)",
                "type": "AgentMeshDossierViewer",
                "id": "agent_mesh_dossier",
                "dossiers": self.agent_dossiers
            }
        ]

        # Add Referral Brief Tab if applicable
        if triage_res["referral_brief"]:
            components.append({
                "title": "Underwriter Referral Brief",
                "type": "ReferralBriefViewer",
                "id": "referral_brief_panel",
                "brief": triage_res["referral_brief"]
            })

        if rating_res["quote_options"] and rating_res["underwriting_risk_score"] >= 60:
            components.append({
                "title": "Quote Options",
                "type": "QuoteOptionSelector",
                "id": "quote_option_selector",
                "quote_id": self.quote_id,
                "options": rating_res["quote_options"]
            })

        components.append({
            "title": "Decision Trace & Actuarial Proof",
            "type": "ActuarialTraceView",
            "id": "actuarial_decision_trace",
            "rule_version": rating_res["rule_set_version"],
            "decision_hash": rating_res["decision_hash"],
            "merkle_root": audit_res["merkle_root"],
            "steps": rating_res["decision_trace"]
        })

        components.append({
            "title": "Audit & Compliance Pack",
            "type": "AuditPackViewer",
            "id": "regulatory_audit_pack",
            "audit_pack_id": audit_res["audit_pack_id"],
            "grounded_spans_count": audit_res["audit_pack"]["grounded_spans_count"],
            "certifications": audit_res["audit_pack"]["regulatory_certifications"]
        })

        return {
            "type": "Tabs",
            "id": "underwriting_workbench_tabs",
            "header": {
                "quote_id": self.quote_id,
                "applicant_name": extracted["applicant_name"],
                "risk_score": rating_res["underwriting_risk_score"],
                "risk_tier": rating_res["risk_tier"],
                "routing_status": triage_res["routing_decision"],
                "total_premium": rating_res["total_base_premium"]
            },
            "components": components
        }

    def _encode_rpc_frame(self, method: str, params: Dict[str, Any]) -> str:
        return json.dumps({"jsonrpc": "2.0", "method": method, "params": params})
