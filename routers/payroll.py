# routers/payroll.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from schemas import PayrollStatusResponse, PayslipResponse, EmployeeResponse, PayslipDetailsResponse
from supabase_client import supabase
from dependencies import get_current_employee

router = APIRouter(prefix="/payroll", tags=["Payroll Module"])

@router.get("/history", response_model=List[PayrollStatusResponse])
def get_payroll_history(employee = Depends(get_current_employee)):
    """
    Retrieves the historical list of salary payroll entries for the employee.
    """
    try:
        response = supabase.table("payroll_status").select("*").eq("employee_id", employee["id"]).order("payment_date", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch payroll history: {str(e)}"
        )

@router.get("/payslips/{payslip_no}", response_model=PayslipResponse)
def get_payslip_details(payslip_no: str, employee = Depends(get_current_employee)):
    """
    Retrieves the complete details of a specific payslip, including gross earnings,
    deductions breakups, net pay, and employee metadata.
    """
    try:
        # Fetch payroll status
        payroll_res = supabase.table("payroll_status").select("*").eq("payslip_no", payslip_no).eq("employee_id", employee["id"]).execute()
        if not payroll_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payslip '{payslip_no}' not found for this employee."
            )
            
        payroll = payroll_res.data[0]
        
        # Fetch detailed payslip items
        details_res = supabase.table("payslip_details").select("*").eq("payroll_status_id", payroll["id"]).execute()
        if not details_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Salary details not found for payslip ID '{payroll['id']}'."
            )
            
        details = details_res.data[0]
        
        # Structure the response
        return PayslipResponse(
            payroll=PayrollStatusResponse(**payroll),
            details=PayslipDetailsResponse(**details),
            employee=EmployeeResponse(**employee)
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load payslip details: {str(e)}"
        )

@router.post("/report")
def request_payroll_report(file_format: str, employee = Depends(get_current_employee)):
    """
    Generates and downloads payroll history reports.
    """
    filename = f"Payroll_Report_{employee['employee_id']}.{file_format.lower()}"
    file_path = f"document-attachments/reports/{filename}"
    return {
        "message": "Payroll report generated successfully.",
        "file_format": file_format,
        "download_url": f"/api/payroll/download/{filename}",
        "file_path": file_path
    }
