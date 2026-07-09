# routers/notifications.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from schemas import NotificationResponse
from supabase_client import supabase
from dependencies import get_current_employee

router = APIRouter(prefix="/notifications", tags=["Notifications Alert Feed"])

@router.get("", response_model=List[NotificationResponse])
def get_my_notifications(unread_only: bool = False, employee = Depends(get_current_employee)):
    """
    Retrieves the list of system notifications for the employee.
    Optional query parameter unread_only filters the alerts feed.
    """
    try:
        query = supabase.table("notifications").select("*").eq("employee_id", employee["id"])
        if unread_only:
            query = query.eq("is_read", False)
        response = query.order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notifications: {str(e)}"
        )

@router.post("/{notification_id}/read")
def mark_notification_as_read(notification_id: int, employee = Depends(get_current_employee)):
    """
    Marks a specific notification as Read.
    """
    try:
        # Check ownership
        check = supabase.table("notifications").select("id").eq("id", notification_id).eq("employee_id", employee["id"]).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found."
            )
            
        supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
        return {"message": "Notification marked as read."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification: {str(e)}"
        )

@router.post("/read-all")
def mark_all_notifications_as_read(employee = Depends(get_current_employee)):
    """
    Marks all notifications for the employee as Read.
    """
    try:
        supabase.table("notifications") \
            .update({"is_read": True}) \
            .eq("employee_id", employee["id"]) \
            .eq("is_read", False) \
            .execute()
        return {"message": "All notifications marked as read."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notifications: {str(e)}"
        )

@router.delete("/{notification_id}")
def delete_notification(notification_id: int, employee = Depends(get_current_employee)):
    """
    Deletes a specific notification from the feed.
    """
    try:
        # Check ownership
        check = supabase.table("notifications").select("id").eq("id", notification_id).eq("employee_id", employee["id"]).execute()
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found."
            )
            
        supabase.table("notifications").delete().eq("id", notification_id).execute()
        return {"message": "Notification deleted successfully."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )

@router.delete("")
def clear_all_notifications(employee = Depends(get_current_employee)):
    """
    Deletes all notifications for the employee.
    """
    try:
        supabase.table("notifications").delete().eq("employee_id", employee["id"]).execute()
        return {"message": "All notifications cleared."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear notifications: {str(e)}"
        )
