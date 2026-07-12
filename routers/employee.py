# routers/employee.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import random
from datetime import date
from schemas import (
    EmployeeResponse, 
    EmployeeUpdate, 
    EmployeeHierarchyResponse, 
    VerificationLetterResponse, 
    VerificationLetterCreate
)
from supabase_client import supabase
from dependencies import get_current_employee

router = APIRouter(prefix="/employees", tags=["Employee Directory"])

@router.get("", response_model=List[EmployeeResponse])
def get_employee_directory(employee = Depends(get_current_employee)):
    """
    Returns a list of all active employees (excluding the current employee) for directory lookup.
    """
    try:
        response = supabase.table("employees").select("*").neq("id", employee["id"]).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch employee directory: {str(e)}"
        )

@router.get("/me", response_model=EmployeeResponse)
def get_my_profile(employee = Depends(get_current_employee)):
    """
    Returns the currently authenticated employee's profile details.
    """
    return employee

@router.put("/me", response_model=EmployeeResponse)
def update_my_profile(profile_data: EmployeeUpdate, employee = Depends(get_current_employee)):
    """
    Updates the personal details of the current employee.
    """
    # Extract only the fields that are passed (not None)
    update_dict = {k: v for k, v in profile_data.model_dump(exclude_unset=True).items() if v is not None}
    
    if not update_dict:
        return employee
        
    try:
        # Format dates to string
        for k, v in update_dict.items():
            if isinstance(v, date):
                update_dict[k] = v.isoformat()
                
        response = supabase.table("employees").update(update_dict).eq("id", employee["id"]).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found or could not be updated."
            )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )

@router.get("/me/hierarchy", response_model=EmployeeHierarchyResponse)
def get_my_hierarchy(employee = Depends(get_current_employee)):
    """
    Returns the organizational hierarchy starting from the current employee
    up to their manager, CTO, and CEO.
    """
    try:
        # Start building hierarchy
        # Alex Rivera (EMP-2048) -> John Smith (Reporting Manager) -> CTO -> CEO
        current_node = EmployeeHierarchyResponse(
            id=employee["id"],
            employee_id=employee["employee_id"],
            full_name=employee["full_name"],
            designation=employee["designation"],
            photo_url=employee.get("photo_url")
        )
        
        # Traverse up the reporting manager tree
        manager_id = employee.get("reporting_manager_id")
        temp_node = current_node
        
        while manager_id:
            mgr_res = supabase.table("employees").select("*").eq("id", manager_id).execute()
            if not mgr_res.data:
                break
            
            mgr = mgr_res.data[0]
            mgr_node = EmployeeHierarchyResponse(
                id=mgr["id"],
                employee_id=mgr["employee_id"],
                full_name=mgr["full_name"],
                designation=mgr["designation"],
                photo_url=mgr.get("photo_url")
            )
            temp_node.manager = mgr_node
            
            # Go up one level
            temp_node = mgr_node
            manager_id = mgr.get("reporting_manager_id")
            
        return current_node
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load hierarchy: {str(e)}"
        )

@router.get("/me/documents")
def get_my_assigned_documents(employee = Depends(get_current_employee)):
    """
    Returns the list of PDF documents assigned to the employee
    (Offer Letter, Contract, NDA, Employee Handbook) as shown in Figma.
    """
    # In a full system, these files might be uploaded to Supabase Storage
    # For now, we return mock metadata and download links
    return [
        {
            "name": "Offer Letter",
            "type": "PDF",
            "url": f"/api/employees/me/documents/offer-letter",
            "status": "ACCEPTED",
            "file_size": "245 KB"
        },
        {
            "name": "Employment Contract",
            "type": "PDF",
            "url": f"/api/employees/me/documents/contract",
            "status": "ACTIVE",
            "file_size": "312 KB"
        },
        {
            "name": "NDA",
            "type": "PDF",
            "url": f"/api/employees/me/documents/nda",
            "status": "ACTIVE",
            "file_size": "312 KB"
        },
        {
            "name": "Employee Handbook",
            "type": "PDF",
            "url": f"/api/employees/me/documents/handbook",
            "status": "ACTIVE",
            "file_size": "1.8 MB"
        }
    ]

@router.get("/me/verification-letters", response_model=List[VerificationLetterResponse])
def get_my_verification_letters(employee = Depends(get_current_employee)):
    """
    Retrieves previous request entries for Employment Verification Letters.
    """
    try:
        response = supabase.table("verification_letters").select("*").eq("employee_id", employee["id"]).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch verification letters: {str(e)}"
        )

@router.post("/me/verification-letters", response_model=VerificationLetterResponse, status_code=status.HTTP_201_CREATED)
def request_verification_letter(letter_data: VerificationLetterCreate, employee = Depends(get_current_employee)):
    """
    Submits a new request for an Employment Verification Letter and auto-generates it.
    """
    try:
        # Generate custom request ID e.g., EVL-2024-XXXX
        rand_num = random.randint(1000, 9999)
        request_id = f"EVL-2024-{rand_num}"
        
        # Mock file path where the generated PDF will reside (in Supabase storage bucket)
        file_name = f"EVL_{employee['employee_id']}_{rand_num}.pdf"
        file_path = f"document-attachments/verification_letters/{file_name}"
        
        insert_data = {
            "request_id": request_id,
            "employee_id": employee["id"],
            "purpose": letter_data.purpose,
            "recipient": letter_data.recipient,
            "email": letter_data.email,
            "address": letter_data.address,
            "additional_notes": letter_data.additional_notes,
            "status": "Generated",
            "requested_on": date.today().isoformat(),
            "generated_on": date.today().isoformat(),
            "generated_by": "System",
            "file_path": file_path
        }
        
        response = supabase.table("verification_letters").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request could not be submitted."
            )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request failed: {str(e)}"
        )
