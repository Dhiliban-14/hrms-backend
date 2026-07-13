# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Adjust import path to find main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from dependencies import get_current_employee

# Setup Mock Employee
mock_employee = {
    "id": "11111111-2222-3333-4444-555555555555",
    "employee_id": "EMP-9999",
    "full_name": "Test QA SDET",
    "email": "qasdet@zeai.com",
    "department": "Engineering",
    "designation": "Principal QA Engineer",
    "status": "Active"
}

def override_get_current_employee():
    return mock_employee

# Apply FastAPI dependency override
app.dependency_overrides[get_current_employee] = override_get_current_employee

client = TestClient(app)

def setup_mock_supabase(mock_supabase):
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.or_.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_supabase.table.return_value = mock_table
    return mock_table

@patch("routers.attendance.supabase")
def test_check_in_success(mock_supabase):
    mock_table = setup_mock_supabase(mock_supabase)
    
    mock_insert_res = MagicMock()
    mock_insert_res.data = [{
        "id": 1,
        "employee_id": mock_employee["id"],
        "date": "2026-07-13",
        "check_in": "09:00:00",
        "working_hours": 0.0,
        "status": "PRESENT",
        "remarks": "Web check-in"
    }]
    # First execute call: check existing (returns empty data list)
    # Second execute call: insert today's check-in
    mock_table.execute.side_effect = [MagicMock(data=[]), mock_insert_res]

    response = client.post("/api/attendance/check-in", json={"remarks": "Web check-in"})
    assert response.status_code == 200
    assert response.json()["status"] == "PRESENT"
    assert response.json()["remarks"] == "Web check-in"


@patch("routers.attendance.supabase")
def test_check_in_already_done(mock_supabase):
    mock_table = setup_mock_supabase(mock_supabase)
    mock_table.execute.return_value = MagicMock(data=[{"id": 1}])

    response = client.post("/api/attendance/check-in", json={"remarks": "Web check-in"})
    assert response.status_code == 400
    assert "already checked in" in response.json()["detail"]


def test_leave_request_date_validation():
    # Test that From Date must be on or before To Date
    payload = {
        "leave_type": "Casual Leave",
        "from_date": "2026-07-15",
        "to_date": "2026-07-13",  # Start is after End
        "total_days": 3,
        "session": "Full Day",
        "leave_reason": "Holiday trip"
    }
    response = client.post("/api/leaves/requests", json=payload)
    assert response.status_code == 400
    assert "From Date must be on or before To Date" in response.json()["detail"]


def test_leave_request_negative_days():
    # Test that Total Days must be positive
    payload = {
        "leave_type": "Casual Leave",
        "from_date": "2026-07-13",
        "to_date": "2026-07-15",
        "total_days": -1,  # Negative days exploit
        "session": "Full Day",
        "leave_reason": "Vacation"
    }
    response = client.post("/api/leaves/requests", json=payload)
    assert response.status_code == 400
    assert "Invalid calculated days" in response.json()["detail"]


@patch("routers.leaves.supabase")
def test_leave_request_insufficient_balance(mock_supabase):
    mock_table = setup_mock_supabase(mock_supabase)
    mock_balances = MagicMock()
    mock_balances.data = [{
        "id": 1,
        "employee_id": mock_employee["id"],
        "casual_total": 12.0,
        "casual_used": 11.0,  # Only 1.0 casual leaves available
        "sick_total": 10.0,
        "sick_used": 0.0,
        "earned_total": 20.0,
        "earned_used": 0.0,
        "maternity_total": 90.0,
        "maternity_used": 0.0
    }]
    mock_table.execute.side_effect = [MagicMock(data=[]), mock_balances]

    payload = {
        "leave_type": "Casual Leave",
        "from_date": "2026-07-13",
        "to_date": "2026-07-15",
        "total_days": 3,  # Requesting 3, but only 1 available
        "session": "Full Day",
        "leave_reason": "Travel"
    }
    response = client.post("/api/leaves/requests", json=payload)
    assert response.status_code == 400
    assert "Insufficient leave balance" in response.json()["detail"]


@patch("routers.leaves.supabase")
def test_leave_request_overlapping_requests(mock_supabase):
    mock_table = setup_mock_supabase(mock_supabase)
    # Existing active leave overlaps with requested range
    mock_overlap = MagicMock()
    mock_overlap.data = [{
        "id": 101,
        "from_date": "2026-07-12",
        "to_date": "2026-07-14",
        "status": "Approved",
        "leave_type": "Casual Leave"
    }]
    mock_table.execute.return_value = mock_overlap

    payload = {
        "leave_type": "Casual Leave",
        "from_date": "2026-07-13",
        "to_date": "2026-07-15",
        "total_days": 3,
        "session": "Full Day",
        "leave_reason": "Travel"
    }
    response = client.post("/api/leaves/requests", json=payload)
    assert response.status_code == 400
    assert "Overlapping leave request found" in response.json()["detail"]


@patch("routers.support.supabase")
def test_raise_support_ticket(mock_supabase):
    mock_table = setup_mock_supabase(mock_supabase)

    mock_insert_res = MagicMock()
    mock_insert_res.data = [{
        "id": 1,
        "ticket_id": "TKT-2026-001",
        "employee_id": mock_employee["id"],
        "category": "IT Support",
        "priority": "High",
        "subject": "VPN Disconnecting",
        "description": "My VPN drops connection every 5 minutes",
        "status": "Open",
        "created_at": "2026-07-13T09:00:00Z"
    }]
    mock_table.execute.side_effect = [mock_insert_res, MagicMock(data=[]), mock_insert_res]

    payload = {
        "category": "IT Support",
        "priority": "High",
        "subject": "VPN Disconnecting",
        "description": "My VPN drops connection every 5 minutes"
    }
    response = client.post("/api/support/tickets", json=payload)
    assert response.status_code == 201
    assert response.json()["ticket_id"] == "TKT-2026-001"
    assert response.json()["status"] == "Open"


@patch("routers.inbox.supabase")
def test_send_inbox_message_recipient_not_found(mock_supabase):
    mock_table = setup_mock_supabase(mock_supabase)
    mock_table.execute.return_value = MagicMock(data=[])

    payload = {
        "recipient_id": "88888888-8888-8888-8888-888888888888",
        "subject": "Greeting",
        "message": "Hello employee"
    }
    response = client.post("/api/inbox/messages", json=payload)
    assert response.status_code == 404
    assert "Recipient with ID" in response.json()["detail"]


@patch("routers.payroll.supabase")
def test_get_payroll_history(mock_supabase):
    mock_table = setup_mock_supabase(mock_supabase)
    mock_table.execute.return_value = MagicMock(data=[
        {
            "id": 1,
            "employee_id": mock_employee["id"],
            "pay_period": "Jun 01 - Jun 30, 2026",
            "payment_date": "2026-06-30",
            "net_pay": 95000.0,
            "status": "CREDITED",
            "payslip_no": "PAY-2026-006"
        }
    ])

    response = client.get("/api/payroll/history")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["payslip_no"] == "PAY-2026-006"
    assert response.json()[0]["status"] == "CREDITED"
