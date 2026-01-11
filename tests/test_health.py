"""
Smoke tests for health check endpoints
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test that health endpoint returns OK"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "time" in data


def test_ready_endpoint(client: TestClient):
    """Test that ready endpoint returns system status"""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "faiss_built" in data
    assert "vacancies_count" in data


def test_debug_endpoint(client: TestClient):
    """Test that debug endpoint returns system information"""
    response = client.get("/debug")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "port" in data
    assert "faiss" in data


def test_root_endpoint(client: TestClient):
    """Test that root endpoint is accessible"""
    response = client.get("/")
    # Should return either HTML or JSON
    assert response.status_code == 200



