# routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from schemas import LoginRequest, TokenResponse, ChangePasswordRequest
from supabase_client import supabase
from dependencies import get_current_user, security

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

@router.post("/logout-all")
def logout_all(credentials = Depends(security), user = Depends(get_current_user)):
    """
    Signs out the user globally from all devices/sessions.
    """
    try:
        token = credentials.credentials if credentials else None
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated."
            )
            
        import requests
        from config import settings
        
        headers = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Send POST request to GoTrue API for global logout
        resp = requests.post(
            f"{settings.supabase_url}/auth/v1/logout?scope=global",
            headers=headers
        )
        
        if resp.status_code not in (200, 204, 201):
            raise Exception(resp.json().get("msg", "Failed to invalidate sessions globally."))
            
        return {"status": "success", "message": "Successfully logged out of all devices."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}"
        )
