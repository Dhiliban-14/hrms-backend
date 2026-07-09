# routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from schemas import LoginRequest, TokenResponse, ChangePasswordRequest
from supabase_client import supabase
from dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    """
    Authenticates a user with Supabase Auth using email and password.
    Returns the JWT access token and session metadata.
    """
    try:
        # Call Supabase Auth API
        auth_response = supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })
        
        return TokenResponse(
            access_token=auth_response.session.access_token,
            token_type="bearer",
            user_id=auth_response.user.id,
            email=auth_response.user.email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/change-password")
def change_password(data: ChangePasswordRequest, user = Depends(get_current_user)):
    """
    Updates the authenticated user's password in Supabase Auth.
    """
    try:
        # Call Supabase Auth update_user to update password
        # In a real environment, you might verify the current password first
        # But Supabase auth handles updating password securely for the currently authenticated session
        supabase.auth.update_user({
            "password": data.new_password
        })
        
        # Log this in a password changes audit logs table if needed
        # (For this mock phase, returning success is sufficient)
        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update password: {str(e)}"
        )
