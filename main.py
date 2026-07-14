# main.py
from fastapi import FastAPI, status, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, employee, tasks, attendance, leaves, payroll, support, inbox, notifications, calendar
import logging

logger = logging.getLogger("hrms")

app = FastAPI(
    title="HRMS Employee Portal Backend",
    description="Custom FastAPI backend wrapped around Supabase services for the ZeAL Soft Employee Portal module.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS (Cross-Origin Resource Sharing)
# This allows your friend's frontend app (running on localhost or a domain) 
# to make API calls to your FastAPI backend server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api")
app.include_router(employee.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(leaves.router, prefix="/api")
app.include_router(payroll.router, prefix="/api")
app.include_router(support.router, prefix="/api")
app.include_router(inbox.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Sanitizes HTTPException responses if they are 500s or contain raw error/database terminology.
    """
    is_sensitive = False
    detail_lower = str(exc.detail).lower()
    if exc.status_code >= 500:
        is_sensitive = True
    else:
        sensitive_patterns = ["database", "supabase", "postgres", "sql", "exception", "failed to", "failed retrieve", "error:", "traceback", "keyerror", "typeerror", "psycopg2"]
        if any(p in detail_lower for p in sensitive_patterns):
            is_sensitive = True
            
    if is_sensitive:
        logger.error(f"HTTPException {exc.status_code} on {request.url.path}: {exc.detail}")
        friendly_msg = "An error occurred while processing your request. Please try again later."
        if exc.status_code == 401:
            friendly_msg = "Invalid credentials or expired session. Please log in again."
        elif exc.status_code == 403:
            friendly_msg = "Access denied. You do not have permission to perform this action."
        elif exc.status_code == 404:
            friendly_msg = "The requested information could not be found."
            
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": friendly_msg}
        )
        
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

import traceback
from datetime import datetime

recent_errors = []

@app.exception_handler(Exception)
async def custom_generic_exception_handler(request: Request, exc: Exception):
    """
    Catches all unhandled runtime errors, logs the stack trace internally, and returns a clean HTTP 500.
    """
    tb = traceback.format_exc()
    logger.error(f"Unhandled Exception on {request.url.path}: {str(exc)}", exc_info=True)
    recent_errors.append({
        "timestamp": datetime.now().isoformat(),
        "path": request.url.path,
        "method": request.method,
        "error_type": type(exc).__name__,
        "error_msg": str(exc),
        "traceback": tb
    })
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

@app.get("/api/debug/errors", tags=["System Debug"])
def get_debug_errors():
    """
    Exposes the last recorded traceback logs for remote troubleshooting.
    """
    return recent_errors

@app.get("/", status_code=status.HTTP_200_OK, tags=["System Health"])
def root_check():
    """
    Simple system check endpoint to verify the API server is active.
    """
    return {
        "status": "online",
        "service": "HRMS Employee Portal Backend",
        "database_provider": "Supabase PostgreSQL"
    }
