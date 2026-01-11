"""
Pytest configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture
def test_user_id():
    """Generate a test user ID"""
    import uuid
    return str(uuid.uuid4())


@pytest.fixture
def test_session_id():
    """Generate a test session ID"""
    import uuid
    return str(uuid.uuid4())



