# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase_client import supabase

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the Supabase JWT token passed in the Authorization header.
    Returns the Supabase Auth user object.
    """
    token = credentials.credentials
    try:
        # Call Supabase auth to fetch user details using the access token
        # This validates the token signature and expiration date
        user_response = supabase.auth.get_user(token)
        return user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_employee(user = Depends(get_current_user)):
    """
    Retrieves the employee record from the public.employees table
    corresponding to the authenticated auth user's UUID.
    """
    try:
        # Query employees table using the auth user's UUID (user.id)
        response = supabase.table("employees").select("*").eq("id", user.id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee profile for user ID '{user.id}' was not found in the database."
            )
        return response.data[0] # Return the employee dictionary
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
