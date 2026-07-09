# seed_supabase.py
import os
import sys
from datetime import date, datetime, timedelta
from supabase import create_client, Client

# Check credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Try loading from local config if running directly
    try:
        from config import settings
        SUPABASE_URL = settings.supabase_url
        SUPABASE_KEY = settings.supabase_key
    except ImportError:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are not set.")
        print("Please rename .env.example to .env and fill in your Supabase credentials.")
        sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define UUIDs for seed data
CEO_UUID = "33333333-3333-3333-3333-333333333333"
CTO_UUID = "22222222-2222-2222-2222-222222222222"
MANAGER_UUID = "11111111-1111-1111-1111-111111111111"
ALEX_UUID = "9952f5ae-f2e6-4fe2-90ab-f7ef5d3a8fb5" # Default Alex Rivera UUID

def clean_database():
    print("Cleaning existing database records...")
    tables = [
        "notifications", "messages", "ticket_messages", "tickets", 
        "payslip_details", "payroll_status", "leave_requests", 
        "leave_balances", "attendance", "timesheets", "deliverables",
        "subtasks", "tasks", "announcements", "holidays", "employees"
    ]
    for table in tables:
        try:
            supabase.table(table).delete().neq("id", "-1" if table in ["holidays", "announcements", "tasks", "subtasks", "timesheets", "deliverables", "attendance", "leave_balances", "leave_requests", "payroll_status", "payslip_details", "tickets", "ticket_messages", "messages", "notifications"] else "00000000-0000-0000-0000-000000000000").execute()
        except Exception as e:
            print(f"Error cleaning table {table}: {e}")

def seed_employees():
    print("Seeding employee profiles...")
    
    # 1. CEO
    ceo = {
        "id": CEO_UUID,
        "employee_id": "EMP-0001",
        "full_name": "Mark Henderson",
        "email": "mark.henderson@zeai.com",
        "designation": "Chief Executive Officer",
        "department": "Management",
        "status": "Active"
    }
    
    # 2. CTO
    cto = {
        "id": CTO_UUID,
        "employee_id": "EMP-0010",
        "full_name": "Sarah Jenkins",
        "email": "sarah.jenkins@zeai.com",
        "designation": "Chief Technology Officer",
        "department": "Technology",
        "reporting_manager_id": CEO_UUID,
        "status": "Active"
    }
    
    # 3. Reporting Manager (John Smith)
    manager = {
        "id": MANAGER_UUID,
        "employee_id": "EMP-1024",
        "full_name": "John Smith",
        "email": "john.smith@zeai.com",
        "designation": "Engineering Manager",
        "department": "Engineering",
        "reporting_manager_id": CTO_UUID,
        "status": "Active"
    }
    
    # 4. Employee (Alex Rivera - EMP-2048)
    alex = {
        "id": ALEX_UUID,
        "employee_id": "EMP-2048",
        "full_name": "Alex Rivera",
        "email": "alex.rivera@zeai.com",
        "dob": "1992-03-15",
        "gender": "Male",
        "marital_status": "Single",
        "nationality": "American",
        "date_of_joining": "2022-01-10",
        "blood_group": "O+",
        "pan_number": "ABCDE1234F",
        "aadhaar_number": "1234 5678 9012",
        "emergency_contact_name": "Maria Rivera (Sister)",
        "emergency_contact_phone": "+1 (555) 987-6543",
        "phone_number": "+1 (555) 123-4567",
        "current_address": "742 Evergreen Terrace, San Francisco, CA 94105, USA",
        "permanent_address": "742 Evergreen Terrace, San Francisco, CA 94105, USA",
        "department": "Engineering",
        "designation": "Software Engineer",
        "reporting_manager_id": MANAGER_UUID,
        "work_location": "San Francisco Office",
        "shift": "General Shift (09:00 AM - 06:00 PM)",
        "work_mode": "Hybrid",
        "cost_center": "ENG-001",
        "insurance_provider": "HealthPlus Insurance",
        "status": "Active",
        "photo_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&q=80&w=200"
    }
    
    supabase.table("employees").insert([ceo, cto, manager, alex]).execute()

def seed_holidays():
    print("Seeding holidays...")
    holidays = [
        {"date": "2024-11-01", "day": "Friday", "holiday_name": "All Saints' Day", "occasion": "Christian", "type": "Public Holiday"},
        {"date": "2024-11-12", "day": "Tuesday", "holiday_name": "Diwali", "occasion": "Hindu", "type": "Festival"},
        {"date": "2024-11-15", "day": "Friday", "holiday_name": "Guru Nanak Jayanti", "occasion": "Sikh", "type": "Public Holiday"},
        {"date": "2024-12-25", "day": "Wednesday", "holiday_name": "Christmas Day", "occasion": "Christian", "type": "Public Holiday"},
        {"date": "2025-01-01", "day": "Wednesday", "holiday_name": "New Year's Day", "occasion": "Global", "type": "Public Holiday"},
        {"date": "2025-01-14", "day": "Tuesday", "holiday_name": "Makar Sankranti", "occasion": "Hindu", "type": "Festival"},
        {"date": "2025-01-26", "day": "Sunday", "holiday_name": "Republic Day", "occasion": "National", "type": "Public Holiday"}
    ]
    supabase.table("holidays").insert(holidays).execute()

def seed_announcements():
    print("Seeding announcements...")
    announcements = [
        {
            "title": "Diwali Celebration 2024",
            "content": "We are excited to invite all employees to our annual Diwali Celebration at the main lounge. Join us for traditional festivities, dinner, and music.",
            "priority": "High",
            "category": "Events",
            "author_name": "HR Team",
            "created_at": "2024-10-28T13:00:00Z"
        },
        {
            "title": "System Maintenance Notice",
            "content": "Please be informed that the HRM portal will be undergoing scheduled maintenance this weekend. Access might be intermittent during Saturday night.",
            "priority": "Medium",
            "category": "IT Updates",
            "author_name": "IT Department",
            "created_at": "2024-10-25T10:30:00Z"
        },
        {
            "title": "Updated Remote Work Policy",
            "content": "We have revised our remote work guidelines to offer more flexibility for hybrid teams. Please review the updated handbook section for details.",
            "priority": "Low",
            "category": "HR Policies",
            "author_name": "HR Team",
            "created_at": "2024-10-20T09:00:00Z"
        }
    ]
    supabase.table("announcements").insert(announcements).execute()

def seed_tasks():
    print("Seeding tasks and subtasks...")
    task1 = {
        "title": "Design Dashboard UI",
        "description": "Design and implement the new dashboard UI for the employee portal. The dashboard should be responsive, user-friendly and match brand guidelines.",
        "project_name": "HR Management Portal",
        "creator_id": MANAGER_UUID,
        "assignee_id": ALEX_UUID,
        "priority": "High",
        "status": "In Progress",
        "progress_pct": 60,
        "due_date": "2024-11-20",
        "estimated_hours": 20.00,
        "logged_hours": 12.50
    }
    
    task2 = {
        "title": "Implement Attendance API",
        "description": "Develop and document endpoints for employee check-in, check-out, and monthly logs query.",
        "project_name": "HR Management Portal",
        "creator_id": MANAGER_UUID,
        "assignee_id": ALEX_UUID,
        "priority": "Medium",
        "status": "To Do",
        "progress_pct": 0,
        "due_date": "2024-11-22",
        "estimated_hours": 15.00,
        "logged_hours": 0.00
    }
    
    task3 = {
        "title": "Fix Payroll Calculation Bug",
        "description": "Resolve salary calculations issue when employee leaves occur on weekends.",
        "project_name": "Payroll System",
        "creator_id": MANAGER_UUID,
        "assignee_id": ALEX_UUID,
        "priority": "High",
        "status": "Completed",
        "progress_pct": 100,
        "due_date": "2024-10-18",
        "estimated_hours": 8.00,
        "logged_hours": 8.75
    }

    t1_res = supabase.table("tasks").insert(task1).execute()
    t2_res = supabase.table("tasks").insert(task2).execute()
    supabase.table("tasks").insert(task3).execute()
    
    # Seed subtasks for Task 1
    t1_id = t1_res.data[0]["id"]
    subtasks = [
        {"task_id": t1_id, "title": "Create dashboard layout", "is_completed": True},
        {"task_id": t1_id, "title": "Implement dashboard cards and widgets", "is_completed": True},
        {"task_id": t1_id, "title": "Add charts visualization for task statistics", "is_completed": True},
        {"task_id": t1_id, "title": "Ensure mobile responsiveness", "is_completed": True},
        {"task_id": t1_id, "title": "Connect API integrations", "is_completed": False},
        {"task_id": t1_id, "title": "Conduct user acceptance testing", "is_completed": False}
    ]
    supabase.table("subtasks").insert(subtasks).execute()

def seed_timesheets():
    print("Seeding timesheet logs...")
    timesheets = [
        {
            "employee_id": ALEX_UUID,
            "project_name": "HR Management Portal",
            "task_name": "Design Dashboard UI",
            "date": "2024-10-24",
            "hours_worked": 6.5,
            "description": "Implemented API integration for employee profile module. Designed and developed the UI for profile summary section.",
            "challenges": "Waiting for approval on avatar upload component from the design team. Facing API response delay in local environment.",
            "plan_tomorrow": "Complete the edit profile functionality. Integrate avatar upload API and test the flow.",
            "status": "Submitted"
        },
        {
            "employee_id": ALEX_UUID,
            "project_name": "HR Management Portal",
            "task_name": "Design Dashboard UI",
            "date": "2024-10-23",
            "hours_worked": 6.0,
            "description": "Created mockups for the attendance tracking grid and monthly details page.",
            "status": "Approved"
        }
    ]
    supabase.table("timesheets").insert(timesheets).execute()

def seed_attendance():
    print("Seeding attendance logs...")
    # Seed logs for the past two weeks
    today = date.today()
    logs = []
    
    # Present 20 days, Late 2 days, Absent 1 day
    for i in range(1, 30):
        log_date = today - timedelta(days=i)
        
        # Skip weekends
        if log_date.weekday() in [5, 6]:
            logs.append({
                "employee_id": ALEX_UUID,
                "date": log_date.isoformat(),
                "status": "WEEKEND",
                "remarks": "Weekly Off"
            })
            continue
            
        if i == 5:
            # Late day
            logs.append({
                "employee_id": ALEX_UUID,
                "date": log_date.isoformat(),
                "check_in": "09:20:00",
                "check_out": "18:10:00",
                "working_hours": 8.50,
                "status": "LATE",
                "remarks": "Late by 20 mins due to traffic"
            })
        elif i == 12:
            # Absent day
            logs.append({
                "employee_id": ALEX_UUID,
                "date": log_date.isoformat(),
                "status": "ABSENT",
                "remarks": "Unplanned sick leave"
            })
        else:
            # Normal present day
            logs.append({
                "employee_id": ALEX_UUID,
                "date": log_date.isoformat(),
                "check_in": "08:45:00",
                "check_out": "17:45:00",
                "working_hours": 9.00,
                "status": "PRESENT"
            })
            
    supabase.table("attendance").insert(logs).execute()

def seed_leave_balances_and_requests():
    print("Seeding leave balances and requests...")
    
    balance = {
        "employee_id": ALEX_UUID,
        "casual_used": 0.00,
        "casual_total": 12.00,
        "sick_used": 2.00,
        "sick_total": 10.00,
        "earned_used": 5.00,
        "earned_total": 20.00,
        "maternity_used": 0.00,
        "maternity_total": 90.00
    }
    supabase.table("leave_balances").insert(balance).execute()
    
    requests = [
        {
            "employee_id": ALEX_UUID,
            "leave_type": "Casual Leave",
            "from_date": "2024-05-15",
            "to_date": "2024-05-17",
            "total_days": 3,
            "session": "Full Day",
            "leave_reason": "Personal work",
            "reason_details": "I need to attend to some urgent personal work involving family commitments in my hometown.",
            "status": "Approved",
            "applied_on": "2024-05-10"
        },
        {
            "employee_id": ALEX_UUID,
            "leave_type": "Sick Leave",
            "from_date": "2024-04-28",
            "to_date": "2024-04-29",
            "total_days": 2,
            "session": "Full Day",
            "leave_reason": "Medical",
            "reason_details": "Recovering from viral fever and cold.",
            "status": "Approved",
            "applied_on": "2024-04-28"
        }
    ]
    supabase.table("leave_requests").insert(requests).execute()

def seed_payroll():
    print("Seeding payroll and payslip details...")
    
    pay1 = {
        "employee_id": ALEX_UUID,
        "pay_period": "Oct 01 - Oct 31, 2024",
        "payment_date": "2024-10-30",
        "net_pay": 4250.00,
        "status": "CREDITED",
        "payslip_no": "PS-2024-10-2048"
    }
    
    pay2 = {
        "employee_id": ALEX_UUID,
        "pay_period": "Sep 01 - Sep 30, 2024",
        "payment_date": "2024-09-30",
        "net_pay": 4200.00,
        "status": "CREDITED",
        "payslip_no": "PS-2024-09-2048"
    }

    p1_res = supabase.table("payroll_status").insert(pay1).execute()
    supabase.table("payroll_status").insert(pay2).execute()
    
    p1_id = p1_res.data[0]["id"]
    details = {
        "payroll_status_id": p1_id,
        "basic_salary": 3000.00,
        "hra": 1200.00,
        "transport_allowance": 200.00,
        "special_allowance": 500.00,
        "performance_bonus": 350.00,
        "other_allowances": 100.00,
        "pf": 360.00,
        "professional_tax": 30.00,
        "tds": 580.00,
        "health_insurance": 150.00,
        "loan_emi": 200.00
    }
    supabase.table("payslip_details").insert(details).execute()

def seed_tickets():
    print("Seeding support tickets...")
    
    ticket1 = {
        "ticket_id": "TKT-2024-058",
        "employee_id": ALEX_UUID,
        "category": "Payroll Issue",
        "priority": "High",
        "subject": "Payslip not showing for May 2024",
        "description": "Hi, I am unable to view my payslip for the month of May 2024. It is not showing in the payslip section even though the payroll status is marked as 'Processed'. Please check and help me resolve this issue. Thank you.",
        "status": "In Progress",
        "created_at": "2024-05-24T10:30:00Z"
    }
    
    t1_res = supabase.table("tickets").insert(ticket1).execute()
    t1_id = t1_res.data[0]["id"]
    
    messages = [
        {
            "ticket_id": t1_id,
            "sender_id": ALEX_UUID,
            "sender_name": "Alex Rivera",
            "message": "Hi, I am unable to view my payslip for the month of May 2024. It is not showing in the payslip section even though the payroll status is marked as 'Processed'.",
            "created_at": "2024-05-24T10:30:00Z"
        },
        {
            "ticket_id": t1_id,
            "sender_id": MANAGER_UUID, # Standing in as HR Admin response
            "sender_name": "Priya Sharma (HR Support)",
            "message": "Hi Alex, we're looking into this. This could be due to a delay in final payroll posting. Will update you shortly.",
            "created_at": "2024-05-24T11:05:00Z"
        },
        {
            "ticket_id": t1_id,
            "sender_id": MANAGER_UUID,
            "sender_name": "Priya Sharma (HR Support)",
            "message": "Hi Alex, the issue has been identified and is currently being fixed. You will be able to view your payslip by EOD.",
            "created_at": "2024-05-27T14:15:00Z"
        }
    ]
    supabase.table("ticket_messages").insert(messages).execute()

def seed_inbox_and_notifications():
    print("Seeding inbox messages and notifications...")
    
    # Inbox
    messages = [
        {
            "sender_id": MANAGER_UUID,
            "sender_name": "HR Department",
            "recipient_id": ALEX_UUID,
            "recipient_name": "Alex Rivera",
            "subject": "Leave request approved",
            "message": "Hi Alex, your leave request (LR-2024-0128) for Casual Leave from May 15 - May 17, 2024 has been approved. Total Days: 3 Days. Please check your leave balance for details.",
            "is_read": False,
            "created_at": "2024-05-15T10:30:00Z"
        },
        {
            "sender_id": ALEX_UUID,
            "sender_name": "Alex Rivera",
            "recipient_id": MANAGER_UUID,
            "recipient_name": "HR Department",
            "subject": "Leave request approved",
            "message": "Thank you so much! I will check my leave balance.",
            "is_read": True,
            "created_at": "2024-05-15T10:32:00Z"
        }
    ]
    supabase.table("messages").insert(messages).execute()
    
    # Notifications
    notifications = [
        {
            "employee_id": ALEX_UUID,
            "title": "Leave Request Approved",
            "message": "Your leave request (LR-2024-0128) for Casual Leave from May 15 - May 17, 2024 has been approved.",
            "type": "Leave",
            "is_read": False,
            "created_at": (datetime.now() - timedelta(minutes=10)).isoformat()
        },
        {
            "employee_id": ALEX_UUID,
            "title": "Payroll Processed",
            "message": "Your October 2024 salary has been processed and is ready. You can view your payslip now.",
            "type": "Payroll",
            "is_read": False,
            "created_at": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            "employee_id": ALEX_UUID,
            "title": "Attendance Reminder",
            "message": "You have not marked your attendance today. Please remember to clock in.",
            "type": "Attendance",
            "is_read": True,
            "created_at": (datetime.now() - timedelta(hours=3)).isoformat()
        }
    ]
    supabase.table("notifications").insert(notifications).execute()

def seed_deliverables():
    print("Seeding deliverables...")
    deliverables = [
        {
            "employee_id": ALEX_UUID,
            "project_name": "ZeAI Dashboard Redesign",
            "task_name": "Design Dashboard UI",
            "deliverable_type": "Design Files",
            "description": "Figma design link and exported layout PNGs for the new employee portal dashboard.",
            "version": "1.0.0",
            "due_date": "2024-05-15",
            "visibility": "Private (Only Team)",
            "file_name": "dashboard_v1_layouts.zip",
            "file_size": "24.5 MB",
            "file_path": "timesheet-attachments/dashboard_v1_layouts.zip",
            "status": "Approved"
        }
    ]
    supabase.table("deliverables").insert(deliverables).execute()

if __name__ == "__main__":
    print("Starting database seeding...")
    try:
        clean_database()
        seed_employees()
        seed_holidays()
        seed_announcements()
        seed_tasks()
        seed_timesheets()
        seed_deliverables()
        seed_attendance()
        seed_leave_balances_and_requests()
        seed_payroll()
        seed_tickets()
        seed_inbox_and_notifications()
        print("Database seeded successfully with Figma-accurate mock data!")
    except Exception as e:
        print(f"Error seeding database: {e}")
