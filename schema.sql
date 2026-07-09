-- schema.sql
-- HRMS Database Schema for PostgreSQL (Supabase)

-- Drop tables if they exist (for clean rebuilding during development)
DROP TABLE IF EXISTS public.notifications CASCADE;
DROP TABLE IF EXISTS public.messages CASCADE;
DROP TABLE IF EXISTS public.ticket_messages CASCADE;
DROP TABLE IF EXISTS public.tickets CASCADE;
DROP TABLE IF EXISTS public.payslip_details CASCADE;
DROP TABLE IF EXISTS public.payroll_status CASCADE;
DROP TABLE IF EXISTS public.leave_requests CASCADE;
DROP TABLE IF EXISTS public.verification_letters CASCADE;
DROP TABLE IF EXISTS public.leave_balances CASCADE;
DROP TABLE IF EXISTS public.attendance CASCADE;
DROP TABLE IF EXISTS public.timesheets CASCADE;
DROP TABLE IF EXISTS public.deliverables CASCADE;
DROP TABLE IF EXISTS public.subtasks CASCADE;
DROP TABLE IF EXISTS public.tasks CASCADE;
DROP TABLE IF EXISTS public.announcements CASCADE;
DROP TABLE IF EXISTS public.holidays CASCADE;
DROP TABLE IF EXISTS public.employees CASCADE;

-- 1. Employees Table
CREATE TABLE public.employees (
    id uuid PRIMARY KEY, -- References Supabase auth.users(id)
    employee_id text UNIQUE NOT NULL, -- e.g. EMP-2048
    full_name text NOT NULL,
    email text UNIQUE NOT NULL,
    dob date,
    gender text,
    marital_status text,
    nationality text,
    date_of_joining date,
    blood_group text,
    pan_number text,
    aadhaar_number text,
    emergency_contact_name text,
    emergency_contact_phone text,
    phone_number text,
    current_address text,
    permanent_address text,
    department text,
    designation text,
    reporting_manager_id uuid REFERENCES public.employees(id) ON DELETE SET NULL,
    work_location text,
    shift text,
    work_mode text,
    cost_center text,
    insurance_provider text,
    status text DEFAULT 'Active',
    photo_url text,
    theme_mode text DEFAULT 'Light',
    primary_color text DEFAULT 'Purple',
    display_language text DEFAULT 'English (US)',
    time_zone text DEFAULT '(GMT+05:30) India Standard Time (IST)',
    email_notifications boolean DEFAULT true,
    push_notifications boolean DEFAULT true,
    task_reminders boolean DEFAULT true,
    announcements_notifications boolean DEFAULT true
);

-- 2. Holidays Table
CREATE TABLE public.holidays (
    id serial PRIMARY KEY,
    date date NOT NULL,
    day text NOT NULL,
    holiday_name text NOT NULL,
    occasion text,
    type text NOT NULL -- Public Holiday, Festival
);

-- 3. Announcements Table
CREATE TABLE public.announcements (
    id serial PRIMARY KEY,
    title text NOT NULL,
    content text NOT NULL,
    priority text DEFAULT 'Low', -- High, Medium, Low
    category text DEFAULT 'General', -- General, HR Policies, IT Updates, Events, Other
    author_name text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

-- 4. Tasks Table
CREATE TABLE public.tasks (
    id serial PRIMARY KEY,
    title text NOT NULL,
    description text,
    project_name text NOT NULL,
    creator_id uuid REFERENCES public.employees(id) ON DELETE SET NULL,
    assignee_id uuid REFERENCES public.employees(id) ON DELETE SET NULL,
    priority text DEFAULT 'Normal', -- High, Medium, Low
    status text DEFAULT 'To Do', -- To Do, In Progress, Review, Completed
    progress_pct integer DEFAULT 0 CHECK (progress_pct >= 0 AND progress_pct <= 100),
    due_date date,
    estimated_hours numeric(5, 2) DEFAULT 0.00,
    logged_hours numeric(5, 2) DEFAULT 0.00,
    created_at timestamp with time zone DEFAULT now()
);

-- 5. Subtasks Table
CREATE TABLE public.subtasks (
    id serial PRIMARY KEY,
    task_id integer REFERENCES public.tasks(id) ON DELETE CASCADE NOT NULL,
    title text NOT NULL,
    is_completed boolean DEFAULT false
);

-- 6. Timesheets Table
CREATE TABLE public.timesheets (
    id serial PRIMARY KEY,
    employee_id uuid REFERENCES public.employees(id) ON DELETE CASCADE NOT NULL,
    project_name text NOT NULL,
    task_name text NOT NULL,
    date date NOT NULL,
    hours_worked numeric(4, 2) NOT NULL,
    description text NOT NULL,
    challenges text,
    plan_tomorrow text,
    status text DEFAULT 'Submitted' -- Draft, Submitted, Approved, Rejected
);

-- 7. Attendance Table
CREATE TABLE public.attendance (
    id serial PRIMARY KEY,
    employee_id uuid REFERENCES public.employees(id) ON DELETE CASCADE NOT NULL,
    date date NOT NULL,
    check_in time without time zone,
    check_out time without time zone,
    working_hours numeric(4, 2) DEFAULT 0.00,
    status text NOT NULL, -- PRESENT, LATE, ABSENT, WEEKEND
    remarks text,
    UNIQUE (employee_id, date)
);

-- 8. Leave Balances Table
CREATE TABLE public.leave_balances (
    id serial PRIMARY KEY,
    employee_id uuid REFERENCES public.employees(id) ON DELETE CASCADE UNIQUE NOT NULL,
    casual_used numeric(4, 2) DEFAULT 0.00,
    casual_total numeric(4, 2) DEFAULT 12.00,
    sick_used numeric(4, 2) DEFAULT 2.00,
    sick_total numeric(4, 2) DEFAULT 10.00,
    earned_used numeric(4, 2) DEFAULT 5.00,
    earned_total numeric(4, 2) DEFAULT 20.00,
    maternity_used numeric(4, 2) DEFAULT 0.00,
    maternity_total numeric(4, 2) DEFAULT 90.00
);

-- 9. Leave Requests Table
CREATE TABLE public.leave_requests (
    id serial PRIMARY KEY,
    employee_id uuid REFERENCES public.employees(id) ON DELETE CASCADE NOT NULL,
    leave_type text NOT NULL, -- Casual Leave, Sick Leave, Earned Leave, Maternity Leave
    from_date date NOT NULL,
    to_date date NOT NULL,
    total_days integer NOT NULL,
    session text NOT NULL, -- Full Day, First Half, Second Half
    leave_reason text NOT NULL,
    reason_details text,
    attachment_path text,
    status text DEFAULT 'Pending', -- Pending, Approved, Rejected, Cancelled
    applied_on date DEFAULT current_date
);

-- 9b. Verification Letters Table
CREATE TABLE public.verification_letters (
    id serial PRIMARY KEY,
    request_id text UNIQUE NOT NULL, -- e.g. EVL-2024-0018
    employee_id uuid REFERENCES public.employees(id) ON DELETE CASCADE NOT NULL,
    purpose text NOT NULL,
    recipient text,
    email text,
    address text,
    additional_notes text,
    status text DEFAULT 'Generated',
    requested_on date DEFAULT current_date,
    generated_on date DEFAULT current_date,
    generated_by text DEFAULT 'System',
    file_path text
);

-- 10. Payroll Status Table
CREATE TABLE public.payroll_status (
    id serial PRIMARY KEY,
    employee_id uuid REFERENCES public.employees(id) ON DELETE CASCADE NOT NULL,
    pay_period text NOT NULL, -- e.g. Oct 01 - Oct 31, 2024
    payment_date date,
    net_pay numeric(10, 2) NOT NULL,
    status text NOT NULL, -- CREDITED, ON HOLD, FAILED
    payslip_no text UNIQUE NOT NULL
);

-- 11. Payslip Details Table
CREATE TABLE public.payslip_details (
    id serial PRIMARY KEY,
    payroll_status_id integer REFERENCES public.payroll_status(id) ON DELETE CASCADE UNIQUE NOT NULL,
    basic_salary numeric(10, 2) NOT NULL,
    hra numeric(10, 2) NOT NULL,
    transport_allowance numeric(10, 2) DEFAULT 0.00,
    special_allowance numeric(10, 2) DEFAULT 0.00,
    performance_bonus numeric(10, 2) DEFAULT 0.00,
    other_allowances numeric(10, 2) DEFAULT 0.00,
    pf numeric(10, 2) NOT NULL,
    professional_tax numeric(10, 2) NOT NULL,
    tds numeric(10, 2) NOT NULL,
    health_insurance numeric(10, 2) DEFAULT 0.00,
    loan_emi numeric(10, 2) DEFAULT 0.00
);

-- 12. Tickets Table
CREATE TABLE public.tickets (
    id serial PRIMARY KEY,
    ticket_id text UNIQUE NOT NULL, -- e.g. TKT-2024-058
    employee_id uuid REFERENCES public.employees(id) ON DELETE CASCADE NOT NULL,
    category text NOT NULL, -- Payroll Issue, Leave Issue, Attendance Issue, IT Support
    priority text NOT NULL, -- Low, Normal, High, Urgent
    subject text NOT NULL,
    description text NOT NULL,
    attachment_path text,
    status text DEFAULT 'Open', -- Open, In Progress, Resolved, Closed, Cancelled
    rating integer CHECK (rating >= 1 AND rating <= 5),
    feedback_comment text,
    created_at timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone
);

-- 13. Ticket Messages Table
CREATE TABLE public.ticket_messages (
    id serial PRIMARY KEY,
    ticket_id integer REFERENCES public.tickets(id) ON DELETE CASCADE NOT NULL,
    sender_id uuid REFERENCES public.employees(id) ON DELETE SET NULL,
    sender_name text NOT NULL,
    message text NOT NULL,
    attachment_path text,
    created_at timestamp with time zone DEFAULT now()
);

-- 14. Messages Table
CREATE TABLE public.messages (
    id serial PRIMARY KEY,
    sender_id uuid REFERENCES public.employees(id) ON DELETE SET NULL,
    sender_name text NOT NULL,
    recipient_id uuid REFERENCES public.employees(id) ON DELETE SET NULL,
    recipient_name text NOT NULL,
    subject text NOT NULL,
    message text NOT NULL,
    is_read boolean DEFAULT false,
    attachment_path text,
    created_at timestamp with time zone DEFAULT now()
);

-- 15. Notifications Table
CREATE TABLE public.notifications (
    id serial PRIMARY KEY,
    employee_id uuid REFERENCES public.employees(id) ON DELETE CASCADE NOT NULL,
    title text NOT NULL,
    message text NOT NULL,
    type text NOT NULL, -- Leave, Payroll, Attendance, Task, Project, Announcement, System
    is_read boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);

-- 16. Deliverables Table
CREATE TABLE public.deliverables (
    id serial PRIMARY KEY,
    employee_id uuid REFERENCES public.employees(id) ON DELETE CASCADE NOT NULL,
    project_name text NOT NULL,
    task_name text NOT NULL,
    deliverable_type text NOT NULL, -- e.g. Design Files
    description text,
    version text DEFAULT '1.0.0',
    due_date date,
    visibility text DEFAULT 'Private (Only Team)',
    file_name text NOT NULL,
    file_size text NOT NULL,
    file_path text NOT NULL,
    status text DEFAULT 'Pending', -- Pending, Approved, Revision
    uploaded_at timestamp with time zone DEFAULT now()
);
