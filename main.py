# main.py
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, employee, tasks, attendance, leaves, payroll, support, inbox, notifications, calendar

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
