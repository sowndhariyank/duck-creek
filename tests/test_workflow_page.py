"""
Unit tests for Duck Creek Underwriting Workflow Demo Page.
Verifies route accessibility, template rendering, and critical workflow components.
"""

import pytest
from backend.app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_workflow_page_route(client):
    """Verifies that /workflow returns HTTP 200 and loads the workflow template."""
    response = client.get('/workflow')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert "Duck Creek" in content
    assert "Underwriting Workflow" in content
    assert "Apex Logistics" in content


def test_workflow_pipeline_phases_present(client):
    """Verifies that all 6 core workflow stages are present in the rendered demo page."""
    response = client.get('/workflow')
    content = response.data.decode('utf-8')
    
    # Core workflow milestones
    assert "Document AI" in content
    assert "OFAC" in content or "Clearance" in content
    assert "Appetite" in content
    assert "Symbolic Actuary" in content or "Zero-LLM" in content
    assert "Duck Creek" in content
    assert "Audit Pack" in content or "Merkle" in content


def test_index_links_to_workflow(client):
    """Verifies that the workbench index page includes navigation to the workflow demo."""
    response = client.get('/')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert "/workflow" in content
