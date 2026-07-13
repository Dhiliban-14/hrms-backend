from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase_client import supabase
from typing import Optional
import logging
import traceback

logger = logging.getLogger("hrms")

def handle_exception(e: Exception, context_msg: str, status_code: int = 500):
    """
    Logs detailed raw exception internally and raises a generic, sanitized HTTPException.
    """
    err_detail = f"EXCEPTION: {context_msg} - {str(e)}\n{traceback.format_exc()}"
    logger.error(err_detail)
    print(err_detail)
    raise HTTPException(
        status_code=status_code,
        detail=f"An internal error occurred. Please try again later."
    )

security = HTTPBearer(auto_error=False)

def get_current_user(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Validates the Supabase JWT token passed in the Authorization header or fallback HttpOnly cookie.
    Returns the Supabase Auth user object.
    """
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Call Supabase auth to fetch user details using the access token
        user_response = supabase.auth.get_user(token)
        return user_response.user
    except Exception as e:
        logger.error(f"Auth verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials or expired session.",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_employee(user = Depends(get_current_user)):
    """
    Retrieves the employee record from the public.employees table
    corresponding to the authenticated auth user's UUID.
    """
    try:
        response = supabase.table("employees").select("*").eq("id", user.id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile was not found in the system."
            )
        return response.data[0] # Return the employee dictionary
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to retrieve employee: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while loading your profile details."
        )
