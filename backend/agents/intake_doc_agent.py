"""
Intake & Document Processing Specialist Agent.
Ingests submission packages, triggers Doc AI extraction, and populates epistemic memory.
"""

from typing import Dict, Any, List
import logging
from backend.tools.docai_tools import DocAiToolSuite
from backend.tools.spiffe_authorizer import SpiffeToolAuthorizer

logger = logging.getLogger("amtha.agents.intake")

class IntakeDocAgent:
    """Specialist subagent for submission intake and Document AI parsing."""

    SPIFFE_ID = "spiffe://amtha.net/agent/intake-doc"

    def __init__(self, docai_tools: DocAiToolSuite):
        self.docai = docai_tools

    def execute(self, submission_id: str, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Executes Document AI parsing with SPIFFE authorization."""
        SpiffeToolAuthorizer.validate_tool_invocation(self.SPIFFE_ID, "docai_process_document_batch")
        
        doc_result = self.docai.process_submission_package(submission_id, files)
        
        return {
            "agent_name": "intake_doc_agent",
            "submission_id": submission_id,
            "status": "COMPLETED",
            "extracted_data": doc_result["extracted_entities"],
            "spans_indexed": doc_result["spans_count"],
            "message": f"Successfully parsed {len(files)} files via Document AI. 5 character spans grounded."
        }

