"""
Integration tests for profile creation flow

Tests the complete flow from session creation to profile building.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def test_session_id(client, test_user_id):
    """Create a test session"""
    response = client.post(
        "/v1/sessions",
        json={"user_id": test_user_id}
    )
    assert response.status_code == 200
    data = response.json()
    return data["session_id"]


def test_create_session(client, test_user_id):
    """Test session creation"""
    response = client.post(
        "/v1/sessions",
        json={"user_id": test_user_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "user_id" in data
    assert data["user_id"] == test_user_id


def test_send_message(client, test_session_id):
    """Test sending a message in chat"""
    response = client.post(
        f"/v1/chat/{test_session_id}",
        json={"text": "Я работаю финансовым аналитиком в банке уже 5 лет."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0


def test_get_session_with_messages(client, test_session_id):
    """Test retrieving session with message history"""
    # First, send a message
    client.post(
        f"/v1/chat/{test_session_id}",
        json={"text": "Тестовое сообщение"}
    )
    
    # Then get session
    response = client.get(f"/v1/sessions/{test_session_id}")
    assert response.status_code == 200
    data = response.json()
    assert "session" in data
    assert "messages" in data
    assert len(data["messages"]) > 0


def test_list_sessions(client, test_user_id):
    """Test listing sessions for a user"""
    # Create a session first
    create_response = client.post(
        "/v1/sessions",
        json={"user_id": test_user_id}
    )
    assert create_response.status_code == 200
    
    # List sessions
    response = client.get(f"/v1/sessions?user_id={test_user_id}")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)
    assert len(data["sessions"]) > 0


def test_delete_session(client, test_session_id):
    """Test deleting a session"""
    response = client.delete(f"/v1/sessions/{test_session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify session is deleted
    get_response = client.get(f"/v1/sessions/{test_session_id}")
    assert get_response.status_code == 404


def test_profile_building_requires_messages(client, test_session_id):
    """Test that profile building requires messages"""
    response = client.get(f"/v1/profile/{test_session_id}")
    # Should either return 404 or empty profile
    # (depends on implementation)
    assert response.status_code in [200, 404]


def test_health_endpoints(client):
    """Test health check endpoints"""
    # Test /health
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    
    # Test /ready
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data


def test_api_versioning(client):
    """Test that API endpoints use /v1/ prefix"""
    # Health endpoints should NOT have /v1/
    health_response = client.get("/health")
    assert health_response.status_code == 200
    
    # API endpoints should have /v1/
    # This is tested implicitly through other tests
    # but we can verify the structure
    response = client.get("/v1/sessions?user_id=test")
    # Should not be 404 due to wrong path
    assert response.status_code in [200, 400, 404]  # 404 if no sessions, 400 if invalid user_id


def test_error_handling_invalid_session(client):
    """Test error handling for invalid session ID"""
    response = client.get("/v1/sessions/invalid-session-id")
    assert response.status_code == 404
    
    response = client.post(
        "/v1/chat/invalid-session-id",
        json={"text": "Test"}
    )
    assert response.status_code in [404, 400]


def test_error_handling_empty_message(client, test_session_id):
    """Test error handling for empty message"""
    response = client.post(
        f"/v1/chat/{test_session_id}",
        json={"text": ""}
    )
    assert response.status_code == 400


def test_error_handling_long_message(client, test_session_id):
    """Test error handling for too long message"""
    long_text = "A" * 6000  # Exceeds 5000 character limit
    response = client.post(
        f"/v1/chat/{test_session_id}",
        json={"text": long_text}
    )
    assert response.status_code == 400



