# routers/leaves.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import date
from decimal import Decimal
from schemas import (
    LeaveBalanceResponse, 
    LeaveRequestResponse, 
    LeaveRequestCreate, 
    LeaveReportRequest
)
from supabase_client import supabase
from dependencies import get_current_employee

router = APIRouter(prefix="/leaves", tags=["Leave Management"])

@router.get("/balances", response_model=LeaveBalanceResponse)
def get_my_leave_balances(employee = Depends(get_current_employee)):
    """
    Retrieves the leave balances (Casual, Sick, Earned, Maternity) for the employee.
    """
    try:
        response = supabase.table("leave_balances").select("*").eq("employee_id", employee["id"]).execute()
        if not response.data:
            # If no record exists, create a default one
            default_balance = {
                "employee_id": employee["id"],
                "casual_used": 0.00,
                "casual_total": 12.00,
                "sick_used": 2.00,
                "sick_total": 10.00,
                "earned_used": 5.00,
                "earned_total": 20.00,
                "maternity_used": 0.00,
                "maternity_total": 90.00
            }
            res_insert = supabase.table("leave_balances").insert(default_balance).execute()
            return res_insert.data[0]
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leave balances: {str(e)}"
        )

@router.get("/requests", response_model=List[LeaveRequestResponse])
def get_my_leave_requests(employee = Depends(get_current_employee)):
    """
    Retrieves previous leave requests submitted by the employee.
    """
    try:
        response = supabase.table("leave_requests").select("*").eq("employee_id", employee["id"]).order("applied_on", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leave requests: {str(e)}"
        )

@router.post("/requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def submit_leave_request(req_data: LeaveRequestCreate, employee = Depends(get_current_employee)):
    """
    Submits a new leave request. Verifies if the employee has sufficient balance first,
    then logs the request.
    """
    # Verify calculated days duration matches date range
    calculated_days = (req_data.to_date - req_data.from_date).days + 1
    if calculated_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="From Date must be on or before To Date."
        )
    if req_data.total_days != calculated_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid calculated days. Requested {req_data.total_days} days, but date range duration is {calculated_days} days."
        )

    try:
        # Check for overlapping leave requests (Pending or Approved)
        overlap_res = supabase.table("leave_requests") \
            .select("*") \
            .eq("employee_id", employee["id"]) \
            .in_("status", ["Pending", "Approved"]) \
            .execute()
            
        for lv in overlap_res.data:
            lv_from = date.fromisoformat(lv["from_date"])
            lv_to = date.fromisoformat(lv["to_date"])
            if req_data.from_date <= lv_to and lv_from <= req_data.to_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Overlapping leave request found. You already have an active leave request from {lv['from_date']} to {lv['to_date']}."
                )

        # Check leave balance
        balance_res = supabase.table("leave_balances").select("*").eq("employee_id", employee["id"]).execute()
        if not balance_res.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave balances record not found."
            )
            
        balances = balance_res.data[0]
        leave_type = req_data.leave_type.lower()
        requested_days = float(req_data.total_days)
        
        # Verify sufficient balance
        if "casual" in leave_type:
            used_key, total_key = "casual_used", "casual_total"
        elif "sick" in leave_type:
            used_key, total_key = "sick_used", "sick_total"
        elif "earned" in leave_type:
            used_key, total_key = "earned_used", "earned_total"
        elif "maternity" in leave_type:
            used_key, total_key = "maternity_used", "maternity_total"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported leave type '{req_data.leave_type}'."
            )
            
        current_used = float(balances[used_key])
        total_limit = float(balances[total_key])
        available = total_limit - current_used
        
        if requested_days > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient leave balance. You requested {requested_days} days, but only have {available} days available for {req_data.leave_type}."
            )
            
        # Create request entry
        insert_data = req_data.model_dump()
        insert_data["employee_id"] = employee["id"]
        insert_data["from_date"] = req_data.from_date.isoformat()
        insert_data["to_date"] = req_data.to_date.isoformat()
        insert_data["applied_on"] = date.today().isoformat()
        insert_data["status"] = "Pending"
        
        response = supabase.table("leave_requests").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to submit leave request."
            )
            
        # Update leave balance
        # For a strict system, we might only deduct the balance AFTER approval,
        # but commonly we increment the 'used' balance to hold/reserve it.
        new_used = current_used + requested_days
        supabase.table("leave_balances").update({used_key: new_used}).eq("employee_id", employee["id"]).execute()
        
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Submission failed: {str(e)}"
        )

@router.get("/requests/{request_id}")
def get_leave_request_timeline(request_id: int, employee = Depends(get_current_employee)):
    """
    Retrieves details of a specific leave request, along with status approval timeline
    (Requested -> Team Lead Approved -> HR Approved -> Confirmed) as shown in Figma.
    """
    try:
        response = supabase.table("leave_requests").select("*").eq("id", request_id).eq("employee_id", employee["id"]).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found."
            )
            
        req = response.data[0]
        
        # Build timeline entries
        timeline = [
            {
                "stage": "Leave Requested",
                "status": "COMPLETED",
                "description": "Your application has been successfully submitted to the portal.",
                "timestamp": f"{req['applied_on']} 09:15 AM"
            }
        ]
        
        if req["status"] in ["Approved", "Completed"]:
            timeline.append({
                "stage": "Approved by Team Lead",
                "status": "COMPLETED",
                "description": "Team lead reviewed and approved your leave request for departmental alignment.",
                "approved_by": "John Smith (Team Lead)",
                "timestamp": f"{req['from_date']} 11:20 AM"
            })
            timeline.append({
                "stage": "Approved by HR",
                "status": "COMPLETED",
                "description": "Human Resources has processed the request and updated the central leave ledger.",
                "approved_by": "Sarah Johnson (HR)",
                "timestamp": f"{req['from_date']} 02:45 PM"
            })
            timeline.append({
                "stage": "Leave Confirmed",
                "status": "COMPLETED",
                "description": "The final confirmation notification has been dispatched to your email.",
                "timestamp": f"{req['from_date']} 02:46 PM"
            })
        elif req["status"] == "Rejected":
            timeline.append({
                "stage": "Rejected by Team Lead",
                "status": "REJECTED",
                "description": "Leave request rejected due to project deadlines.",
                "rejected_by": "John Smith (Team Lead)",
                "timestamp": f"{date.today().isoformat()} 11:00 AM"
            })
        else:
            # Pending status
            timeline.append({
                "stage": "Approved by Team Lead",
                "status": "PENDING",
                "description": "Awaiting review by Team Lead.",
                "timestamp": None
            })
            
        return {
            "request_details": req,
            "timeline": timeline
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timeline: {str(e)}"
        )

@router.post("/report")
def request_leave_report(report_data: LeaveReportRequest, employee = Depends(get_current_employee)):
    """
    Exports a leave report. Mocking generation by returning details and file URL path.
    """
    filename = f"Leave_Report_{employee['employee_id']}_{report_data.from_date}_to_{report_data.to_date}.{report_data.file_format.lower()}"
    file_path = f"document-attachments/reports/{filename}"
    
    return {
        "message": "Leave report generated successfully.",
        "report_type": report_data.report_type,
        "date_range": f"{report_data.from_date} to {report_data.to_date}",
        "file_format": report_data.file_format,
        "download_url": f"/api/leaves/download/{filename}",
        "file_path": file_path
    }

@router.delete("/requests")
def clear_my_leave_requests(employee = Depends(get_current_employee)):
    """
    Clears all leave requests and resets leave balances back to 0 for the employee (Demo use).
    """
    try:
        # Delete requests
        supabase.table("leave_requests").delete().eq("employee_id", employee["id"]).execute()
        
        # Reset balances
        supabase.table("leave_balances").update({
            "earned_used": 0,
            "sick_used": 0,
            "casual_used": 0,
            "maternity_used": 0
        }).eq("employee_id", employee["id"]).execute()
        
        return {"message": "All leave requests cleared and balances reset successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear leave requests: {str(e)}"
        )
