# MISSION: BUILD DUCK CREEK UNDERWRITING INTELLIGENCE MULTI-AGENT SYSTEM

You are an expert AI software architect and engineer specializing in the **Google Cloud Agentic Stack (Google ADK 2.x, A2UI, Gemini Enterprise on Vertex AI)**.

Build the complete **Duck Creek Underwriting Intelligence Multi-Agent Platform** from scratch. Write the exact file contents specified below so that the resulting application, automated tests, and glassmorphic UI on `http://localhost:8080` are **100% pixel-perfect identical** and functionally bitwise reproducible.

---

# 1. 🏗️ ARCHITECTURE & SUBAGENTS (13 SPECIALIST AGENTS)

Implement a **Hub-and-Spoke Multi-Agent Topology** with 13 specialized subagents:
- **Lead Supervisor**: `lead_underwriting_orchestrator` (executes Fractal Chain of Thought / FCoT across Macro, Meso, and Micro lenses, managing silent transfers and assembling the dynamic A2UI schema).
- **12 Specialist Workers**:
  1. `intake_doc_agent`: Extracts entity values and character-span bounding boxes from ACORD forms and SOVs using Document AI.
  2. `clearance_sanctions_agent`: Screens entity against U.S. OFAC SDN list and broker duplicate accounts.
  3. `appetite_eligibility_agent`: Validates NAICS 541512 operations against underwriting appetite guides.
  4. `data_enrichment_agent`: Queries Apigee Gateway for FEMA flood maps (Zone X), satellite wildfire index (2.4), and ISO PPC fire protection (Grade 3).
  5. `exposure_analysis_agent`: Evaluates building COPE and estimates Probable Maximum Loss ($3.125M / 25%).
  6. `loss_history_agent`: Analyzes 5-year claims triangles ($0.00 incurred, 0 open claims).
  7. `symbolic_rating_engine`: **Zero-LLM Actuarial Core**. Pure Python rating formulas referencing versioned ISO tables (`RuleSet v2026.3`) with zero LLM calls. Computes Risk Score (**89 / 100**) and Base Premium (**$29,294.62**).
  8. `quote_structuring_agent`: Packages Basic ($25.7k), Preferred ($29.2k, Recommended), and Comprehensive ($35.7k) quote options.
  9. `grounding_compliance_agent`: Mechanical AST claim parser that physically blocks any output if a claim lacks a verified citation.
  10. `triage_referral_agent`: Routes Score >= 85 to Straight-Through Processing (STP) auto-release, and Score 60-84 to the Human Underwriter Referral Queue with an Underwriter Brief.
  11. `quote_lifecycle_agent`: Manages quote FSM states in BigQuery and executes 30-day price-lock TTL watchdogs.
  12. `audit_governance_agent`: Computes cryptographic Merkle tree root hashes over all spans and math traces.

---

# 2. 📁 COMPLETE FILE TREE TO CREATE

```
duck-creek/
├── backend/
│   ├── app.py                             # Flask server & SSE streaming (port 8080)
│   ├── config.py                          # Settings (port 8080, rule version v2026.3)
│   ├── requirements.txt                   # Version-locked dependencies
│   ├── core/
│   │   ├── runtime_stabilizer.py          # A2UI / ADK module stabilizer
│   │   ├── epistemic_memory.py            # Citation store & Merkle root builder
│   │   ├── grounding_guard.py             # AST claim parser & zero-hallucination blocker
│   │   └── state_machine.py               # Quote lifecycle FSM & BigQuery event logger
│   ├── agents/
│   │   ├── orchestrator_agent.py          # Lead FCoT Supervisor Orchestrator
│   │   ├── intake_doc_agent.py            # Doc AI Specialist
│   │   ├── clearance_sanctions_agent.py   # OFAC & CIP Specialist
│   │   ├── appetite_eligibility_agent.py  # Appetite Specialist
│   │   ├── data_enrichment_agent.py       # Hazard & Geospatial Specialist
│   │   ├── exposure_analysis_agent.py     # COPE & PML Specialist
│   │   ├── loss_history_agent.py          # Loss Runs Specialist
│   │   ├── symbolic_rating_engine.py      # Zero-LLM Actuary Core
│   │   ├── quote_structuring_agent.py     # Multi-Tier Quote Specialist
│   │   ├── grounding_compliance_agent.py  # Citation Verification Specialist
│   │   ├── triage_referral_agent.py       # STP vs Referral Specialist
│   │   ├── quote_lifecycle_agent.py       # FSM Lifecycle Specialist
│   │   └── audit_governance_agent.py      # Merkle Audit Specialist
│   ├── tools/
│   │   ├── gcs_tools.py                   # GCS tool suite
│   │   ├── docai_tools.py                 # Document AI tool suite
│   │   ├── bigquery_tools.py              # BigQuery tool suite
│   │   └── spiffe_authorizer.py           # SPIFFE & Envoy security authorizer
│   └── interfaces/
│       ├── apigee_interface.py            # Apigee interface & deterministic mock
│       ├── looker_interface.py            # Looker interface & deterministic mock
│       └── policy_admin_interface.py      # PAS core interface & mock adapter
│
├── frontend/
│   ├── templates/index.html               # Semantic Glassmorphic HTML
│   └── static/
│       ├── css/style.css                  # Dark glassmorphic design system tokens
│       └── js/
│           ├── app.js                     # Reactive SSE consumer & topology visualizer
│           └── workbench.js               # A2UI Dynamic Component Factory & Drill-Down
│
├── samples/
│   ├── sample_submission_apex.json        # Preferred STP Scenario (Score 89)
│   ├── sample_submission_cascade.json     # Referral Queue Scenario (Score 76)
│   ├── sample_submission_timberline.json  # Auto-Decline Scenario (Score 42)
│   ├── generate_sample_pdfs.py            # Native pure-Python script generating sample PDFs
│   └── documents/                         # ACORD 125, ACORD 140, SOV, Loss Runs PDFs
│
├── infra/terraform/
│   ├── main.tf, variables.tf, security.tf, outputs.tf
│
└── tests/
    ├── test_symbolic_determinism.py       # 10,000-run bitwise reproducibility test
    ├── test_mechanical_grounding.py       # AST blocker test
    ├── test_quote_lifecycle_fsm.py        # FSM lifecycle test
    ├── test_spiffe_security.py            # Down-scoped tool test
    └── test_sse_api_stream.py             # SSE streaming compliance test
```

---

# 3. 🎨 EXACT FRONTEND CODE TO WRITE (VERBATIM)

To guarantee exact pixel-perfect identical UI on all machines, write the following frontend files verbatim:

### `frontend/templates/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Duck Creek Underwriting Intelligence | Google Cloud Agentic Stack</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
</head>
<body class="theme-dark">
    <div class="workbench-layout">
        <header class="workbench-header">
            <div class="header-brand">
                <div class="brand-logo">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#4285F4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M2 17L12 22L22 17" stroke="#34A853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M2 12L12 17L22 12" stroke="#FBBC05" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="brand-text">
                    <h1>DUCK CREEK UNDERWRITING INTELLIGENCE</h1>
                    <span class="platform-tag">Google ADK 2.x • A2UI • Gemini Enterprise • Zero-LLM Actuary</span>
                </div>
            </div>

            <div class="header-controls">
                <div class="submission-selector-wrapper">
                    <label for="submissionSelect">Active Submission:</label>
                    <select id="submissionSelect" class="form-select">
                        <option value="SUB-2026-90412">SUB-2026-90412: Apex Logistics Solutions (Preferred - 89 pts)</option>
                        <option value="SUB-2026-90881">SUB-2026-90881: Cascade Cold Storage (Referral - 76 pts)</option>
                        <option value="SUB-2026-91004">SUB-2026-91004: Timberline Millwork (Declined - 42 pts)</option>
                    </select>
                </div>

                <div class="status-badge-container">
                    <span id="badgeScore" class="badge badge-score">Score: --</span>
                    <span id="badgeTier" class="badge badge-tier">Tier: --</span>
                    <span id="badgeRouting" class="badge badge-routing">Decision: Pending</span>
                </div>

                <button id="btnRunUnderwriting" class="btn btn-primary">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                    Run Underwriting Stream
                </button>
            </div>
        </header>

        <main class="workbench-main">
            <aside class="panel topology-panel">
                <div class="panel-header">
                    <h2>Multi-Agent Mesh Topology</h2>
                    <span class="badge badge-live">13 Agents Live</span>
                </div>
                <div class="topology-subtext">Click any node to inspect its I/O Dossier</div>
                <div class="mesh-tree" id="meshTree">
                    <div class="mesh-node node-supervisor" id="node_lead_underwriting_orchestrator">
                        <div class="node-indicator"></div>
                        <div class="node-label">
                            <strong>Lead Underwriting Orchestrator</strong>
                            <small>FCoT Supervisor Engine</small>
                        </div>
                    </div>
                    <div class="worker-nodes-grid">
                        <div class="mesh-node node-worker" id="node_intake_doc_agent"><span class="worker-badge">01</span> Intake Doc AI</div>
                        <div class="mesh-node node-worker" id="node_clearance_sanctions_agent"><span class="worker-badge">02</span> OFAC Clearance</div>
                        <div class="mesh-node node-worker" id="node_appetite_eligibility_agent"><span class="worker-badge">03</span> Appetite NAICS</div>
                        <div class="mesh-node node-worker" id="node_data_enrichment_agent"><span class="worker-badge">04</span> Apigee Hazard</div>
                        <div class="mesh-node node-worker" id="node_exposure_analysis_agent"><span class="worker-badge">05</span> COPE Exposure</div>
                        <div class="mesh-node node-worker" id="node_loss_history_agent"><span class="worker-badge">06</span> Loss History</div>
                        <div class="mesh-node node-worker node-actuary" id="node_symbolic_rating_engine"><span class="worker-badge">07</span> Symbolic Actuary</div>
                        <div class="mesh-node node-worker" id="node_quote_structuring_agent"><span class="worker-badge">08</span> Quote Structuring</div>
                        <div class="mesh-node node-worker node-guard" id="node_grounding_compliance_agent"><span class="worker-badge">09</span> Grounding Guard</div>
                        <div class="mesh-node node-worker" id="node_triage_referral_agent"><span class="worker-badge">10</span> Triage STP</div>
                        <div class="mesh-node node-worker" id="node_quote_lifecycle_agent"><span class="worker-badge">11</span> Quote Lifecycle</div>
                        <div class="mesh-node node-worker" id="node_audit_governance_agent"><span class="worker-badge">12</span> Audit Governance</div>
                    </div>
                </div>

                <div class="telemetry-box">
                    <div class="telemetry-title">Live Stream Telemetry</div>
                    <div id="telemetryFeed" class="telemetry-feed"></div>
                </div>
            </aside>

            <section class="panel dynamic-panel">
                <div class="panel-header">
                    <h2>Explainable Underwriting Workbench</h2>
                    <span class="platform-tag">Dynamic A2UI Engine</span>
                </div>
                <div id="dynamicA2uiContainer" class="dynamic-a2ui-container">
                    <div class="welcome-card">
                        <div class="welcome-icon">🏛️</div>
                        <h3>Underwriting Session Ready</h3>
                        <p>Select an active submission package above and click <strong>"Run Underwriting Stream"</strong> to initiate the Fractal Chain of Thought (FCoT) multi-agent pipeline.</p>
                        <div class="feature-pills">
                            <span class="pill">⚡ &lt; 15s STP Auto-Quote</span>
                            <span class="pill">🛡️ Zero Hallucinations</span>
                            <span class="pill">🧮 100% Deterministic Math</span>
                            <span class="pill">🔗 1-Click PDF Citations</span>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <aside id="evidenceDrawer" class="evidence-drawer hidden">
            <div class="drawer-header">
                <h3>Source Document Evidence</h3>
                <button id="btnCloseDrawer" class="btn-icon">&times;</button>
            </div>
            <div id="drawerBody" class="drawer-body"></div>
        </aside>
    </div>

    <script src="/static/js/workbench.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

---

# 4. ⚙️ SETUP & LAUNCH INSTRUCTIONS

1. Write out the complete codebase and sample documents.
2. Run `python samples/generate_sample_pdfs.py` to create the standard PDF submission packages in `samples/documents/`.
3. Set up a Python 3.9+ virtual environment (`.venv`), install `requirements.txt`, and run `PYTHONPATH=. pytest tests/ -v` (assert 17/17 tests passing).
4. Start the server using `PYTHONPATH=. python backend/app.py` in background daemon mode on port `8080`.
5. Verify `/api/health` returns `{"status": "HEALTHY", "service": "duck-creek-underwriting-agent"}` and ensure the web interface is accessible on `http://localhost:8080`.
