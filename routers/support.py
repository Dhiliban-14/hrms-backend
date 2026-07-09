# routers/support.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import random
from datetime import datetime
from schemas import (
    TicketResponse, 
    TicketCreate, 
    TicketFeedback, 
    TicketMessageResponse, 
    TicketMessageCreate
)
from supabase_client import supabase
from dependencies import get_current_employee

router = APIRouter(prefix="/support", tags=["Employee Support (Tickets)"])

@router.get("/faqs")
def get_faqs():
    """
    Returns Frequently Asked Questions (FAQs) and User Guides.
    """
    return [
        {
            "category": "Leave Management",
            "questions": [
                {
                    "question": "How do I apply for casual leave?",
                    "answer": "Go to the Leave module, select 'Apply Leave', fill in the type of leave as Casual Leave, select the dates, and submit. It will update your balance and notify your manager."
                },
                {
                    "question": "How long does it take for leave approval?",
                    "answer": "Leaves are reviewed by your Team Lead first, then approved by HR. Usually takes 24-48 hours."
                }
            ]
        },
        {
            "category": "Payroll & Payslips",
            "questions": [
                {
                    "question": "When is my payslip available?",
                    "answer": "Monthly payslips are generated and uploaded by HR on the last working day of the month."
                },
                {
                    "question": "How do I download my payslip?",
                    "answer": "Go to the Payroll Status module, view the payslip details, and click the 'Download PDF' button."
                }
            ]
        },
        {
            "category": "Help & IT Support",
            "questions": [
                {
                    "question": "How do I raise a support ticket?",
                    "answer": "Go to Support Ticket Management, click 'Raise Ticket', choose a category, write a description, and submit. You can track progress and chat with the agent."
                }
            ]
        }
    ]

@router.get("/contact-hr")
def get_contact_hr():
    """
    Returns official Contact HR Information.
    """
    return {
        "email": "hr@zeai.com",
        "phone": "+1 (555) 019-2834",
        "working_hours": "9:00 AM - 6:00 PM (Monday - Friday)",
        "office_location": "ZeAI Head Office, Building A, Floor 4"
    }

@router.get("/tickets", response_model=List[TicketResponse])
def get_my_support_tickets(employee = Depends(get_current_employee)):
    """
    Retrieves all support tickets raised by the employee.
    """
    try:
        response = supabase.table("tickets").select("*, ticket_messages(*)").eq("employee_id", employee["id"]).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tickets: {str(e)}"
        )

@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket_details(ticket_id: str, employee = Depends(get_current_employee)):
    """
    Retrieves detailed info and chat history messages for a specific support ticket.
    """
    try:
        response = supabase.table("tickets").select("*, ticket_messages(*)").eq("ticket_id", ticket_id).eq("employee_id", employee["id"]).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket '{ticket_id}' not found."
            )
        ticket = response.data[0]
        # Sort messages by created_at time
        ticket["messages"] = sorted(ticket.get("ticket_messages", []), key=lambda m: m.get("created_at"))
        return ticket
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ticket details: {str(e)}"
        )

@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def raise_support_ticket(ticket_data: TicketCreate, employee = Depends(get_current_employee)):
    """
    Submits a new support ticket.
    """
    try:
        # Generate custom Ticket ID e.g., TKT-2024-058
        rand_num = random.randint(100, 999)
        ticket_id = f"TKT-2024-{rand_num:03d}"
        
        insert_data = {
            "ticket_id": ticket_id,
            "employee_id": employee["id"],
            "category": ticket_data.category,
            "priority": ticket_data.priority,
            "subject": ticket_data.subject,
            "description": ticket_data.description,
            "status": "Open"
        }
        
        response = supabase.table("tickets").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket could not be submitted."
            )
            
        ticket = response.data[0]
        
        # Insert initial conversation message (description)
        msg_data = {
            "ticket_id": ticket["id"],
            "sender_id": employee["id"],
            "sender_name": employee["full_name"],
            "message": ticket_data.description,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("ticket_messages").insert(msg_data).execute()
        
        return get_ticket_details(ticket_id, employee)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit ticket: {str(e)}"
        )

@router.post("/tickets/{ticket_id}/messages", response_model=TicketMessageResponse, status_code=status.HTTP_201_CREATED)
def post_ticket_message(ticket_id: str, msg_data: TicketMessageCreate, employee = Depends(get_current_employee)):
    """
    Sends a new message inside a ticket conversation chat thread.
    """
    try:
        # Fetch ticket ID
        t_res = supabase.table("tickets").select("id, status").eq("ticket_id", ticket_id).eq("employee_id", employee["id"]).execute()
        if not t_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket '{ticket_id}' not found."
            )
            
        ticket = t_res.data[0]
        if ticket["status"] in ["Closed", "Cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This ticket is closed. Reopen the ticket to post new messages."
            )
            
        insert_data = {
            "ticket_id": ticket["id"],
            "sender_id": employee["id"],
            "sender_name": employee["full_name"],
            "message": msg_data.message,
            "attachment_path": msg_data.attachment_path,
            "created_at": datetime.now().isoformat()
        }
        
        # If employee replies, set status to In Progress (if it was Open/Resolved)
        if ticket["status"] == "Resolved":
            supabase.table("tickets").update({"status": "In Progress"}).eq("id", ticket["id"]).execute()
            
        response = supabase.table("ticket_messages").insert(insert_data).execute()
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to post message: {str(e)}"
        )

@router.post("/tickets/{ticket_id}/feedback")
def submit_ticket_feedback(ticket_id: str, feedback: TicketFeedback, employee = Depends(get_current_employee)):
    """
    Submits a rating and comment on a ticket after it has been marked as Resolved, and Closes it.
    """
    try:
        t_res = supabase.table("tickets").select("id, status").eq("ticket_id", ticket_id).eq("employee_id", employee["id"]).execute()
        if not t_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket '{ticket_id}' not found."
            )
            
        ticket = t_res.data[0]
        update_data = {
            "rating": feedback.rating,
            "feedback_comment": feedback.feedback_comment,
            "status": "Closed"
        }
        
        response = supabase.table("tickets").update(update_data).eq("id", ticket["id"]).execute()
        return {"message": "Feedback submitted and ticket closed successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}"
        )

@router.post("/tickets/{ticket_id}/reopen")
def reopen_ticket(ticket_id: str, employee = Depends(get_current_employee)):
    """
    Reopens a Closed or Resolved ticket.
    """
    try:
        t_res = supabase.table("tickets").select("id").eq("ticket_id", ticket_id).eq("employee_id", employee["id"]).execute()
        if not t_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket '{ticket_id}' not found."
            )
            
        ticket = t_res.data[0]
        supabase.table("tickets").update({"status": "In Progress"}).eq("id", ticket["id"]).execute()
        return {"message": f"Ticket '{ticket_id}' has been reopened."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reopening failed: {str(e)}"
        )
