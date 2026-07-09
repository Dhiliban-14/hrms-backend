# routers/inbox.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime
from schemas import MessageResponse, MessageCreate
from supabase_client import supabase
from dependencies import get_current_employee

router = APIRouter(prefix="/inbox", tags=["Messaging & Inbox"])

@router.get("/threads")
def get_my_chat_threads(employee = Depends(get_current_employee)):
    """
    Returns a summary list of the most recent messages grouped by conversation partner.
    (Matches the Inbox sidebar view in Figma 'img_44').
    """
    try:
        # Fetch all messages involving the current employee as sender or recipient
        emp_id = employee["id"]
        response = supabase.table("messages") \
            .select("*") \
            .or_(f"sender_id.eq.{emp_id},recipient_id.eq.{emp_id}") \
            .order("created_at", desc=True) \
            .execute()
            
        messages = response.data
        
        # Group by conversation partner (the user who is not "me")
        threads = {}
        for msg in messages:
            # Determine partner details
            is_sender = (msg["sender_id"] == emp_id)
            partner_id = msg["recipient_id"] if is_sender else msg["sender_id"]
            partner_name = msg["recipient_name"] if is_sender else msg["sender_name"]
            
            if partner_id not in threads:
                # Count unread messages (if received and not read)
                unread_count = 1 if (not is_sender and not msg["is_read"]) else 0
                
                threads[partner_id] = {
                    "partner_id": partner_id,
                    "partner_name": partner_name,
                    "last_message": msg["message"],
                    "last_subject": msg["subject"],
                    "timestamp": msg["created_at"],
                    "unread_count": unread_count
                }
            else:
                # Accumulate unread counts for older messages in the thread
                if not is_sender and not msg["is_read"]:
                    threads[partner_id]["unread_count"] += 1
                    
        return list(threads.values())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load chat threads: {str(e)}"
        )

@router.get("/threads/{partner_id}", response_model=List[MessageResponse])
def get_conversation_history(partner_id: str, employee = Depends(get_current_employee)):
    """
    Retrieves the chronological message history between the current employee and a partner.
    Also marks all received messages in this thread as Read.
    """
    emp_id = employee["id"]
    try:
        # Fetch conversation messages
        response = supabase.table("messages") \
            .select("*") \
            .or_(f"and(sender_id.eq.{emp_id},recipient_id.eq.{partner_id}),and(sender_id.eq.{partner_id},recipient_id.eq.{emp_id})") \
            .order("created_at", desc=False) \
            .execute()
            
        messages = response.data
        
        # Mark received messages as read
        received_unread_ids = [
            msg["id"] for msg in messages 
            if msg["recipient_id"] == emp_id and not msg["is_read"]
        ]
        
        if received_unread_ids:
            # Perform batch update
            supabase.table("messages") \
                .update({"is_read": True}) \
                .in_("id", received_unread_ids) \
                .execute()
                
            # Update local read state in return list
            for msg in messages:
                if msg["id"] in received_unread_ids:
                    msg["is_read"] = True
                    
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversation history: {str(e)}"
        )

@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(msg_data: MessageCreate, employee = Depends(get_current_employee)):
    """
    Sends a new message to another employee or department.
    """
    try:
        # Verify recipient exists
        rec_res = supabase.table("employees").select("id, full_name").eq("id", msg_data.recipient_id).execute()
        if not rec_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient with ID '{msg_data.recipient_id}' not found."
            )
            
        recipient = rec_res.data[0]
        
        insert_data = {
            "sender_id": employee["id"],
            "sender_name": employee["full_name"],
            "recipient_id": recipient["id"],
            "recipient_name": recipient["full_name"],
            "subject": msg_data.subject,
            "message": msg_data.message,
            "attachment_path": msg_data.attachment_path,
            "is_read": False,
            "created_at": datetime.now().isoformat()
        }
        
        response = supabase.table("messages").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send message."
            )
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )
