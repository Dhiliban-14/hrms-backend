# routers/attendance.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import date, datetime, time
from decimal import Decimal
from schemas import AttendanceResponse, CheckInRequest, CheckOutRequest, AttendanceReportRequest
from supabase_client import supabase
from dependencies import get_current_employee

router = APIRouter(prefix="/attendance", tags=["Attendance Management"])

@router.get("", response_model=List[AttendanceResponse])
def get_my_attendance_logs(start_date: Optional[date] = None, end_date: Optional[date] = None, employee = Depends(get_current_employee)):
    """
    Retrieves attendance logs for the logged-in employee.
    Optional query parameters let the client filter by a date range.
    """
    try:
        query = supabase.table("attendance").select("*").eq("employee_id", employee["id"])
        if start_date:
            query = query.gte("date", start_date.isoformat())
        if end_date:
            query = query.lte("date", end_date.isoformat())
        response = query.order("date", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch attendance logs: {str(e)}"
        )

@router.get("/metrics")
def get_attendance_metrics(employee = Depends(get_current_employee)):
    """
    Returns aggregated metrics for the current month:
    Present Days, Absent Days, Late Days, Overtime Hours, and Total Working Hours.
    """
    try:
        today = date.today()
        start_of_month = date(today.year, today.month, 1).isoformat()
        
        response = supabase.table("attendance") \
            .select("*") \
            .eq("employee_id", employee["id"]) \
            .gte("date", start_of_month) \
            .execute()
            
        logs = response.data
        present_count = sum(1 for log in logs if log["status"] in ["PRESENT", "LATE"])
        late_count = sum(1 for log in logs if log["status"] == "LATE")
        absent_count = sum(1 for log in logs if log["status"] == "ABSENT")
        
        total_hours = sum(float(log["working_hours"] or 0) for log in logs)
        
        # Simple overtime calculation: anything over 8 hours a day is overtime
        overtime_hours = sum(max(0, float(log["working_hours"] or 0) - 8.0) for log in logs)
        
        return {
            "present_days": present_count,
            "absent_days": absent_count,
            "late_days": late_count,
            "overtime_hours": round(overtime_hours, 1),
            "total_working_hours": round(total_hours, 1)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {str(e)}"
        )

@router.post("/check-in", response_model=AttendanceResponse)
def check_in(req: CheckInRequest, employee = Depends(get_current_employee)):
    """
    Registers a check-in event for today. If the check-in is after 09:00 AM,
    the status is marked as 'LATE' instead of 'PRESENT'.
    """
    today_date = date.today().isoformat()
    now_time = datetime.now().time()
    
    # Define Shift Start: 09:00:00
    shift_start = time(9, 0, 0)
    status_str = "PRESENT"
    if now_time > shift_start:
        status_str = "LATE"
        
    try:
        # Check if already checked in today
        check_existing = supabase.table("attendance").select("*").eq("employee_id", employee["id"]).eq("date", today_date).execute()
        if check_existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already checked in today."
            )
            
        insert_data = {
            "employee_id": employee["id"],
            "date": today_date,
            "check_in": now_time.strftime("%H:%M:%S"),
            "working_hours": 0.00,
            "status": status_str,
            "remarks": req.remarks
        }
        
        response = supabase.table("attendance").insert(insert_data).execute()
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Check-in failed: {str(e)}"
        )

@router.post("/check-out", response_model=AttendanceResponse)
def check_out(req: CheckOutRequest, employee = Depends(get_current_employee)):
    """
    Registers a check-out event for today and calculates the working hours.
    """
    today_date = date.today().isoformat()
    now_time = datetime.now().time()
    
    try:
        # Fetch today's check-in log
        log_res = supabase.table("attendance").select("*").eq("employee_id", employee["id"]).eq("date", today_date).execute()
        if not log_res.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No check-in record found for today. Please check-in first."
            )
            
        log = log_res.data[0]
        if log.get("check_out"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already checked out today."
            )
            
        check_in_str = log["check_in"]
        # Convert time strings to datetime objects for calculation
        fmt = "%H:%M:%S"
        t_in = datetime.strptime(check_in_str, fmt)
        t_out = datetime.strptime(now_time.strftime(fmt), fmt)
        
        # Calculate working hours (difference in seconds divided by 3600)
        tdelta = t_out - t_in
        hours = round(tdelta.total_seconds() / 3600.0, 2)
        
        # Update log
        update_data = {
            "check_out": now_time.strftime(fmt),
            "working_hours": float(hours),
            "remarks": req.remarks if req.remarks else log.get("remarks")
        }
        
        response = supabase.table("attendance").update(update_data).eq("id", log["id"]).execute()
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Check-out failed: {str(e)}"
        )

@router.post("/report")
def request_attendance_report(report_data: AttendanceReportRequest, employee = Depends(get_current_employee)):
    """
    Exports attendance report for a specified format.
    Mocking generation by returning details and file URL path.
    """
    # Mock file path in Supabase storage bucket
    filename = f"Attendance_Report_{employee['employee_id']}_{report_data.date_range_start}_to_{report_data.date_range_end}.{report_data.file_format.lower()}"
    file_path = f"document-attachments/reports/{filename}"
    
    return {
        "message": "Report generated successfully.",
        "report_type": report_data.report_type,
        "date_range": f"{report_data.date_range_start} to {report_data.date_range_end}",
        "file_format": report_data.file_format,
        "download_url": f"/api/attendance/download/{filename}",
        "file_path": file_path
    }

@router.delete("/today")
def delete_today_attendance(employee = Depends(get_current_employee)):
    """
    Deletes today's attendance log for the logged-in employee (useful for testing/demo).
    """
    try:
        today_date = date.today().isoformat()
        supabase.table("attendance").delete().eq("employee_id", employee["id"]).eq("date", today_date).execute()
        return {"message": "Today's attendance log reset successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset attendance: {str(e)}"
        )
