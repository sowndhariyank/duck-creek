"""
SSE Streaming & REST Endpoints Integration Test Suite.
Verifies HTTP endpoints, SSE event construction, and JSON-RPC schema compliance.
"""

import json
import pytest
from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client

def test_health_check_endpoint(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "duck-creek-underwriting-agent"
    assert data["rule_version"] == "v2026.3"


def test_submission_upload_endpoint(client):
    response = client.post('/api/submissions/upload', json={"submission_id": "SUB-TEST-999"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "UPLOAD_ACCEPTED"
    assert data["submission_id"] == "SUB-TEST-999"


def test_sse_stream_compliance(client):
    """Verifies that the /api/chat/stream endpoint returns text/event-stream with valid JSON-RPC frames."""
    response = client.post('/api/chat/stream', json={
        "prompt": "Evaluate submission SUB-TEST-999",
        "submission_id": "SUB-TEST-999"
    })
    assert response.status_code == 200
    assert "text/event-stream" in response.headers['Content-Type']
    
    raw_text = response.get_data(as_text=True)
    lines = [line.strip() for line in raw_text.split("\n\n") if line.strip().startswith("data:")]
    
    assert len(lines) > 5, "Expected multiple SSE event frames in stream!"
    
    # Parse first frame
    first_frame_data = json.loads(lines[0].replace("data:", "").strip())
    assert first_frame_data["jsonrpc"] == "2.0"
    assert "method" in first_frame_data
    assert "params" in first_frame_data
    
    # Check that onUiComponentDelivery is emitted
    methods_emitted = [json.loads(l.replace("data:", "").strip())["method"] for l in lines]
    assert "onAgentThought" in methods_emitted
    assert "onAgentDelegation" in methods_emitted
    assert "onToolCall" in methods_emitted
    assert "onUiComponentDelivery" in methods_emitted


def test_bind_quote_endpoint(client):
    response = client.post('/api/quotes/Q-2026-90412/bind', json={
        "tier": "Preferred (Recommended)",
        "payment_schedule": "ANNUAL"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "BOUND"
    assert "policy_number" in data

