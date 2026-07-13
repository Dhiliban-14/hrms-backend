-- Migration: Add missing B-tree indexes for foreign keys in HRMS schema
-- Target: Optimize joins, searches, and integrity updates

-- 1. Employees reporting manager (self-referencing FK)
CREATE INDEX IF NOT EXISTS idx_employees_reporting_manager ON public.employees(reporting_manager_id);

-- 2. Tasks creator and assignee indexes
CREATE INDEX IF NOT EXISTS idx_tasks_creator ON public.tasks(creator_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON public.tasks(assignee_id);

-- 3. Subtasks task reference
CREATE INDEX IF NOT EXISTS idx_subtasks_task ON public.subtasks(task_id);

-- 4. Timesheets employee reference
CREATE INDEX IF NOT EXISTS idx_timesheets_employee ON public.timesheets(employee_id);

-- 5. Attendance employee reference
CREATE INDEX IF NOT EXISTS idx_attendance_employee ON public.attendance(employee_id);

-- 6. Leave requests employee reference
CREATE INDEX IF NOT EXISTS idx_leave_requests_employee ON public.leave_requests(employee_id);

-- 7. Verification letters employee reference
CREATE INDEX IF NOT EXISTS idx_verification_letters_employee ON public.verification_letters(employee_id);

-- 8. Payroll status employee reference
CREATE INDEX IF NOT EXISTS idx_payroll_status_employee ON public.payroll_status(employee_id);

-- 9. Payslip details payroll status reference
CREATE INDEX IF NOT EXISTS idx_payslip_details_payroll_status ON public.payslip_details(payroll_status_id);

-- 10. Tickets employee reference
CREATE INDEX IF NOT EXISTS idx_tickets_employee ON public.tickets(employee_id);

-- 11. Ticket messages references
CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON public.ticket_messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_messages_sender ON public.ticket_messages(sender_id);

-- 12. Messages sender and recipient references
CREATE INDEX IF NOT EXISTS idx_messages_sender ON public.messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON public.messages(recipient_id);

-- 13. Notifications employee reference
CREATE INDEX IF NOT EXISTS idx_notifications_employee ON public.notifications(employee_id);

-- 14. Deliverables employee reference
CREATE INDEX IF NOT EXISTS idx_deliverables_employee ON public.deliverables(employee_id);
