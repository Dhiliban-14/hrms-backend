# routers/calendar.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from supabase_client import supabase
from dependencies import get_current_employee

router = APIRouter(prefix="/calendar", tags=["Calendar Events"])

class CalendarEvent(BaseModel):
    id: str
    title: str
    start_date: str
    end_date: Optional[str] = None
    type: str # Holiday, Meeting, Company Event, Important Update, Personal
    description: Optional[str] = None
    color: str # Hex color representation

@router.get("/events", response_model=List[CalendarEvent])
def get_calendar_events(employee = Depends(get_current_employee)):
    try:
        events = []
        
        # 1. Fetch holidays
        hol_res = supabase.table("holidays").select("*").execute()
        for hol in hol_res.data:
            events.append(CalendarEvent(
                id=f"holiday-{hol['id']}",
                title=hol['holiday_name'],
                start_date=hol['date'],
                type="Holiday",
                description=hol.get('occasion') or "Public Holiday",
                color="#ba1a1a"
            ))
            
        # 2. Fetch employee's leave requests (Approved)
        leave_res = supabase.table("leave_requests").select("*").eq("employee_id", employee["id"]).eq("status", "Approved").execute()
        for lv in leave_res.data:
            events.append(CalendarEvent(
                id=f"leave-{lv['id']}",
                title=f"{lv['leave_type']} Approved",
                start_date=lv['from_date'],
                end_date=lv['to_date'],
                type="Personal",
                description=lv.get('leave_reason') or "Approved Leave",
                color="#797488"
            ))
            
        # 3. Fetch employee's tasks
        task_res = supabase.table("tasks").select("*").eq("assignee_id", employee["id"]).execute()
        for tk in task_res.data:
            if tk.get("due_date"):
                events.append(CalendarEvent(
                    id=f"task-{tk['id']}",
                    title=f"Task Due: {tk['title']}",
                    start_date=tk['due_date'],
                    type="Important Update",
                    description=tk.get('description') or "Task deadline",
                    color="#593600"
                ))

        # 4. Standard Figma static events for demo (November 2024)
        demo_events = [
            CalendarEvent(
                id="demo-meeting-1",
                title="Team Meeting",
                start_date="2024-11-05",
                type="Meeting",
                description="Weekly progress alignment sync.",
                color="#006c49"
            ),
            CalendarEvent(
                id="demo-payroll-1",
                title="Payroll Processing",
                start_date="2024-11-15",
                type="Important Update",
                description="Monthly payroll calculations check.",
                color="#593600"
            ),
            CalendarEvent(
                id="demo-policy-1",
                title="HR Policy Review",
                start_date="2024-11-18",
                type="Important Update",
                description="Annual employee handbook guidelines update.",
                color="#593600"
            ),
            CalendarEvent(
                id="demo-planning-1",
                title="Q4 Planning Meeting",
                start_date="2024-11-20",
                type="Meeting",
                description="Review targets and strategies for Q4.",
                color="#006c49"
            ),
            CalendarEvent(
                id="demo-maintenance-1",
                title="System Maintenance",
                start_date="2024-11-28",
                type="Important Update",
                description="Database optimization and portal upgrade.",
                color="#593600"
            )
        ]
        
        events.extend(demo_events)
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load calendar events: {str(e)}"
        )
