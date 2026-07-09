# routers/tasks.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from decimal import Decimal
from datetime import date
from schemas import (
    TaskResponse, 
    TaskUpdate, 
    TimesheetResponse, 
    TimesheetCreate, 
    TimesheetUpdate,
    DeliverableResponse,
    DeliverableCreate
)
from supabase_client import supabase
from dependencies import get_current_employee

router = APIRouter(prefix="/tasks", tags=["Tasks & Timesheets"])

@router.get("", response_model=List[TaskResponse])
def get_my_tasks(status_filter: Optional[str] = None, employee = Depends(get_current_employee)):
    """
    Returns list of tasks assigned to the current employee.
    Can optionally filter by task status (e.g. 'To Do', 'In Progress').
    """
    try:
        query = supabase.table("tasks").select("*, subtasks(*)").eq("assignee_id", employee["id"])
        if status_filter:
            query = query.eq("status", status_filter)
        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}"
        )

@router.get("/{task_id}", response_model=TaskResponse)
def get_task_details(task_id: int, employee = Depends(get_current_employee)):
    """
    Retrieves detailed info of a specific task including subtasks checklist.
    """
    try:
        response = supabase.table("tasks").select("*, subtasks(*)").eq("id", task_id).eq("assignee_id", employee["id"]).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found or not assigned to you."
            )
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task: {str(e)}"
        )

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskUpdate, employee = Depends(get_current_employee)):
    """
    Updates status, progress percentage, or logged hours of an assigned task.
    """
    update_dict = {k: v for k, v in task_data.model_dump(exclude_unset=True).items() if v is not None}
    if not update_dict:
        return get_task_details(task_id, employee)
        
    try:
        # Check task assignment first
        task_check = supabase.table("tasks").select("id, logged_hours").eq("id", task_id).eq("assignee_id", employee["id"]).execute()
        if not task_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or not assigned to you."
            )
            
        # If logged_hours is being updated, we accumulate it
        if "logged_hours" in update_dict:
            current_logged = Decimal(str(task_check.data[0]["logged_hours"]))
            new_add = Decimal(str(update_dict["logged_hours"]))
            update_dict["logged_hours"] = float(current_logged + new_add)
            
        response = supabase.table("tasks").update(update_dict).eq("id", task_id).execute()
        
        # Re-fetch with subtasks
        return get_task_details(task_id, employee)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )

@router.post("/{task_id}/subtasks/{subtask_id}/toggle")
def toggle_subtask(task_id: int, subtask_id: int, employee = Depends(get_current_employee)):
    """
    Toggles a subtask completion check.
    """
    try:
        # Verify task is assigned to the current employee
        task_check = supabase.table("tasks").select("id").eq("id", task_id).eq("assignee_id", employee["id"]).execute()
        if not task_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or not assigned to you."
            )
            
        # Get current subtask status
        sub_check = supabase.table("subtasks").select("is_completed").eq("id", subtask_id).eq("task_id", task_id).execute()
        if not sub_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtask not found for this task."
            )
            
        new_status = not sub_check.data[0]["is_completed"]
        
        response = supabase.table("subtasks").update({"is_completed": new_status}).eq("id", subtask_id).execute()
        return {"subtask_id": subtask_id, "is_completed": new_status}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle subtask: {str(e)}"
        )

# --- Timesheets ---
@router.get("/timesheets/history", response_model=List[TimesheetResponse])
def get_my_timesheets(employee = Depends(get_current_employee)):
    """
    Retrieves logged timesheets for the current employee.
    """
    try:
        response = supabase.table("timesheets").select("*").eq("employee_id", employee["id"]).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve timesheets: {str(e)}"
        )

@router.post("/timesheets", response_model=TimesheetResponse, status_code=status.HTTP_201_CREATED)
def create_timesheet_log(timesheet_data: TimesheetCreate, employee = Depends(get_current_employee)):
    """
    Logs a new daily work progress (timesheet entry).
    """
    try:
        insert_data = timesheet_data.model_dump()
        insert_data["employee_id"] = employee["id"]
        insert_data["date"] = timesheet_data.date.isoformat()
        insert_data["hours_worked"] = float(timesheet_data.hours_worked)
        
        response = supabase.table("timesheets").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timesheet entry could not be created."
            )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logging timesheet failed: {str(e)}"
        )

# --- Deliverables ---
@router.get("/deliverables/history", response_model=List[DeliverableResponse])
def get_my_deliverables(employee = Depends(get_current_employee)):
    """
    Retrieves all deliverables uploaded by the employee.
    """
    try:
        response = supabase.table("deliverables").select("*").eq("employee_id", employee["id"]).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch deliverables: {str(e)}"
        )

@router.post("/deliverables", response_model=DeliverableResponse, status_code=status.HTTP_201_CREATED)
def upload_deliverable(deliverable_data: DeliverableCreate, employee = Depends(get_current_employee)):
    """
    Logs the submission of a new project deliverable.
    """
    try:
        insert_data = deliverable_data.model_dump()
        insert_data["employee_id"] = employee["id"]
        insert_data["due_date"] = deliverable_data.due_date.isoformat() if deliverable_data.due_date else None
        
        response = supabase.table("deliverables").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deliverable record could not be created."
            )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Uploading deliverable failed: {str(e)}"
        )
