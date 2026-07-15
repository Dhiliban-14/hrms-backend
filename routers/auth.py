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
        # 1. Verify current password by signing in
        try:
            auth_res = supabase.auth.sign_in_with_password({
                "email": user.email,
                "password": data.current_password
            })
            token = auth_res.session.access_token
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password."
            )
            
        # 2. Update password using the access token
        import requests
        from config import settings
        
        headers = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "password": data.new_password
        }
        res = requests.put(f"{settings.supabase_url}/auth/v1/user", json=payload, headers=headers)
        if res.status_code != 200:
            raise Exception(res.json().get("msg", res.text))
            
        return {"message": "Password updated successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update password: {str(e)}"
        )
