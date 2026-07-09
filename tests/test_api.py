# tests/test_api.py
from fastapi.testclient import TestClient
import sys
import os

# Adjust import path to find main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_root_check():
    """
    Verifies that the root health check endpoint is active and returns online status.
    """
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "online"
    assert json_data["service"] == "HRMS Employee Portal Backend"
    assert json_data["database_provider"] == "Supabase PostgreSQL"

def test_auth_endpoints_exist():
    """
    Verifies that the auth login routes return validation errors rather than 404,
    confirming that the router is registered correctly.
    """
    # Empty POST body should fail with validation error (422 Unprocessable Entity)
    # instead of 404 Not Found
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 422
