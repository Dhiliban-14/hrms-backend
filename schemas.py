# schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, time, datetime
from decimal import Decimal

# --- Authentication ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# --- Employee schemas ---
class EmployeeBase(BaseModel):
    employee_id: str
    full_name: str
    email: EmailStr
    dob: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    date_of_joining: Optional[date] = None
    blood_group: Optional[str] = None
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    phone_number: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    reporting_manager_id: Optional[str] = None # UUID string
    work_location: Optional[str] = None
    shift: Optional[str] = None
    work_mode: Optional[str] = None
    cost_center: Optional[str] = None
    insurance_provider: Optional[str] = None
    status: Optional[str] = "Active"
    photo_url: Optional[str] = None
    theme_mode: Optional[str] = "Light"
    primary_color: Optional[str] = "Purple"
    display_language: Optional[str] = "English (US)"
    time_zone: Optional[str] = "(GMT+05:30) India Standard Time (IST)"
    email_notifications: Optional[bool] = True
    push_notifications: Optional[bool] = True
    task_reminders: Optional[bool] = True
    announcements_notifications: Optional[bool] = True

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    blood_group: Optional[str] = None
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    phone_number: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    insurance_provider: Optional[str] = None
    photo_url: Optional[str] = None
    theme_mode: Optional[str] = None
    primary_color: Optional[str] = None
    display_language: Optional[str] = None
    time_zone: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    task_reminders: Optional[bool] = None
    announcements_notifications: Optional[bool] = None

class EmployeeResponse(EmployeeBase):
    id: str # UUID string

class EmployeeHierarchyResponse(BaseModel):
    id: str
    employee_id: str
    full_name: str
    designation: str
    photo_url: Optional[str] = None
    manager: Optional["EmployeeHierarchyResponse"] = None

# --- Holidays ---
class HolidayResponse(BaseModel):
    id: int
    date: date
    day: str
    holiday_name: str
    occasion: Optional[str] = None
    type: str

# --- Announcements ---
class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    priority: str
    category: str
    author_name: str
    created_at: datetime

# --- Tasks & Subtasks ---
class SubtaskBase(BaseModel):
    title: str
    is_completed: bool = False

class SubtaskCreate(SubtaskBase):
    pass

class SubtaskResponse(SubtaskBase):
    id: int
    task_id: int

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    project_name: str
    priority: str = "Normal" # High, Medium, Low
    status: str = "To Do" # To Do, In Progress, Review, Completed
    progress_pct: int = 0
    due_date: Optional[date] = None
    estimated_hours: Decimal = Decimal("0.00")
    logged_hours: Decimal = Decimal("0.00")

class TaskCreate(TaskBase):
    assignee_id: Optional[str] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    progress_pct: Optional[int] = None
    logged_hours: Optional[Decimal] = None

class TaskResponse(TaskBase):
    id: int
    creator_id: Optional[str] = None
    assignee_id: Optional[str] = None
    created_at: datetime
    subtasks: List[SubtaskResponse] = []

# --- Timesheets ---
class TimesheetBase(BaseModel):
    project_name: str
    task_name: str
    date: date
    hours_worked: Decimal
    description: str
    challenges: Optional[str] = None
    plan_tomorrow: Optional[str] = None
    status: str = "Submitted"

class TimesheetCreate(TimesheetBase):
    pass

class TimesheetUpdate(BaseModel):
    hours_worked: Optional[Decimal] = None
    description: Optional[str] = None
    challenges: Optional[str] = None
    plan_tomorrow: Optional[str] = None
    status: Optional[str] = None

class TimesheetResponse(TimesheetBase):
    id: int
    employee_id: str

# --- Deliverables ---
class DeliverableBase(BaseModel):
    project_name: str
    task_name: str
    deliverable_type: str
    description: Optional[str] = None
    version: str = "1.0.0"
    due_date: Optional[date] = None
    visibility: str = "Private (Only Team)"

class DeliverableCreate(DeliverableBase):
    file_name: str
    file_size: str
    file_path: str

class DeliverableResponse(DeliverableBase):
    id: int
    employee_id: str
    file_name: str
    file_size: str
    file_path: str
    status: str
    uploaded_at: datetime

# --- Attendance ---
class AttendanceBase(BaseModel):
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    working_hours: Optional[Decimal] = Decimal("0.00")
    status: str # PRESENT, LATE, ABSENT, WEEKEND
    remarks: Optional[str] = None

class AttendanceResponse(AttendanceBase):
    id: int
    employee_id: str

class CheckInRequest(BaseModel):
    remarks: Optional[str] = None

class CheckOutRequest(BaseModel):
    remarks: Optional[str] = None

class AttendanceReportRequest(BaseModel):
    report_type: str # Daily Attendance, Monthly Summary, Late/Early Report, Absenteeism, Overtime
    date_range_start: date
    date_range_end: date
    file_format: str # PDF, Excel, CSV

# --- Leaves ---
class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: str
    casual_used: Decimal
    casual_total: Decimal
    sick_used: Decimal
    sick_total: Decimal
    earned_used: Decimal
    earned_total: Decimal
    maternity_used: Decimal
    maternity_total: Decimal

class LeaveRequestBase(BaseModel):
    leave_type: str # Casual Leave, Sick Leave, Earned Leave, Maternity Leave
    from_date: date
    to_date: date
    total_days: int
    session: str # Full Day, First Half, Second Half
    leave_reason: str
    reason_details: Optional[str] = None
    attachment_path: Optional[str] = None
    status: str = "Pending"

class LeaveRequestCreate(BaseModel):
    leave_type: str
    from_date: date
    to_date: date
    total_days: int
    session: str
    leave_reason: str
    reason_details: Optional[str] = None

class LeaveRequestResponse(LeaveRequestBase):
    id: int
    employee_id: str
    applied_on: date
class LeaveReportRequest(BaseModel):
    report_type: str
    from_date: date
    to_date: date
    file_format: str

# --- Verification Letters ---
class VerificationLetterBase(BaseModel):
    purpose: str
    recipient: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    additional_notes: Optional[str] = None

class VerificationLetterCreate(VerificationLetterBase):
    pass

class VerificationLetterResponse(VerificationLetterBase):
    id: int
    request_id: str
    employee_id: str
    status: str
    requested_on: date
    generated_on: date
    generated_by: str
    file_path: Optional[str] = None

# --- Payroll ---
class PayslipDetailsResponse(BaseModel):
    id: int
    payroll_status_id: int
    basic_salary: Decimal
    hra: Decimal
    transport_allowance: Decimal
    special_allowance: Decimal
    performance_bonus: Decimal
    other_allowances: Decimal
    pf: Decimal
    professional_tax: Decimal
    tds: Decimal
    health_insurance: Decimal
    loan_emi: Decimal

class PayrollStatusResponse(BaseModel):
    id: int
    employee_id: str
    pay_period: str
    payment_date: Optional[date] = None
    net_pay: Decimal
    status: str # CREDITED, ON HOLD, FAILED
    payslip_no: str

class PayslipResponse(BaseModel):
    payroll: PayrollStatusResponse
    details: PayslipDetailsResponse
    employee: EmployeeResponse

# --- Support Tickets ---
class TicketBase(BaseModel):
    ticket_id: str
    category: str # Payroll Issue, Leave Issue, Attendance Issue, IT Support
    priority: str # Low, Normal, High, Urgent
    subject: str
    description: str
    attachment_path: Optional[str] = None
    status: str = "Open"

class TicketCreate(BaseModel):
    category: str
    priority: str
    subject: str
    description: str

class TicketFeedback(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback_comment: Optional[str] = None

class TicketMessageBase(BaseModel):
    message: str
    attachment_path: Optional[str] = None

class TicketMessageCreate(TicketMessageBase):
    pass

class TicketMessageResponse(TicketMessageBase):
    id: int
    ticket_id: int
    sender_id: Optional[str] = None
    sender_name: str
    created_at: datetime

class TicketResponse(TicketBase):
    id: int
    employee_id: str
    rating: Optional[int] = None
    feedback_comment: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    messages: List[TicketMessageResponse] = []

# --- Messages / Inbox ---
class MessageBase(BaseModel):
    subject: str
    message: str
    attachment_path: Optional[str] = None

class MessageCreate(MessageBase):
    recipient_id: str # UUID of recipient

class MessageResponse(MessageBase):
    id: int
    sender_id: Optional[str] = None
    sender_name: str
    recipient_id: Optional[str] = None
    recipient_name: str
    is_read: bool
    created_at: datetime

# --- Notifications ---
class NotificationResponse(BaseModel):
    id: int
    employee_id: str
    title: str
    message: str
    type: str # Leave, Payroll, Attendance, Task, Project, Announcement, System
    is_read: bool
    created_at: datetime

# Handle self-referential Pydantic schemas in hierarchy
EmployeeHierarchyResponse.model_rebuild()
