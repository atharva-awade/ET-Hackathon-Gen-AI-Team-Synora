"""
Mock Enterprise Tool Implementations
Simulates JIRA, Email, Calendar, HR Portal, Approval Systems
"""
import random
import json
from datetime import datetime, timedelta

# ─── Mock Enterprise Databases ────────────────────────────────────────────────

EMPLOYEES_DB = {
    "EMP001": {"name": "Arjun Sharma",    "role": "Senior Engineer",    "dept": "Engineering", "email": "arjun.sharma@techcorp.in",    "manager": "EMP003"},
    "EMP002": {"name": "Priya Patel",     "role": "Product Manager",    "dept": "Product",     "email": "priya.patel@techcorp.in",     "manager": "EMP006"},
    "EMP003": {"name": "Rahul Verma",     "role": "Engineering Manager","dept": "Engineering", "email": "rahul.verma@techcorp.in",     "manager": "EMP007"},
    "EMP004": {"name": "Sunita Krishnan", "role": "HR Manager",         "dept": "HR",          "email": "sunita.krishnan@techcorp.in", "manager": "EMP007"},
    "EMP005": {"name": "Vikram Nair",     "role": "IT Admin",           "dept": "IT",          "email": "vikram.nair@techcorp.in",     "manager": "EMP007"},
    "EMP006": {"name": "Deepak Menon",    "role": "VP Product",         "dept": "Product",     "email": "deepak.menon@techcorp.in",    "manager": "EMP007"},
    "EMP007": {"name": "Kavitha Reddy",   "role": "CTO",                "dept": "Leadership",  "email": "kavitha.reddy@techcorp.in",   "manager": None},
    "NEW001": {"name": "Ananya Gupta",    "role": "Backend Engineer",   "dept": "Engineering", "email": "ananya.gupta@techcorp.in",    "manager": "EMP003"},
}

SYSTEMS = ["github", "slack", "jira", "hr_portal", "gsuite"]

APPROVAL_REQUESTS = {
    "PR-2847": {
        "title": "Vendor Contract Renewal — TechSupplies Ltd",
        "amount": 450000,
        "requestor": "EMP002",
        "primary_approver": "EMP006",   # This person is ON LEAVE
        "created_at": (datetime.now() - timedelta(hours=49)).isoformat(),
        "status": "pending",
        "sla_hours": 24,
        "category": "Procurement",
    }
}

EMPLOYEES_ON_LEAVE = ["EMP006"]

MEETING_TRANSCRIPTS = {
    "MTG-SPRINT-42": {
        "title": "Q2 Sprint Planning — Team Nexus",
        "date": "2026-03-28",
        "participants": ["Arjun Sharma (EMP001)", "Priya Patel (EMP002)", "Rahul Verma (EMP003)", "Ananya Gupta (NEW001)"],
        "transcript": """
Rahul: Alright team, let's review our sprint goals. Arjun, where are we on the payment gateway integration?

Arjun: We're about 70% done. I need to finish the retry logic and write unit tests. Should be done by Wednesday.

Rahul: Great. Priya, what about the user onboarding redesign?

Priya: The wireframes are approved. I need Arjun's team to implement the new flow. Also, someone needs to update the analytics dashboard to track the new funnel — but I'm not sure who owns that.

Rahul: That's a good point — we need to figure out the analytics ownership. Ananya, you just joined, but since you'll be working on the backend, can you take a look at the payment retry logic with Arjun?

Ananya: Sure, happy to help. I'll sync with Arjun today.

Rahul: Also, we need to schedule a security review before the payment feature goes live. That should involve the security team — Priya, can you coordinate that?

Priya: Will do. I'll reach out to the security team this week.

Rahul: One more thing — the mobile app crash reports from last week. Someone needs to investigate and fix the crash on Android 12. This is critical.

Arjun: I can take that. Let me triage it first and then fix.

Rahul: Perfect. Let's all update JIRA by end of day. See everyone next week.
        """,
    }
}

# ─── JIRA Error Injection State ───────────────────────────────────────────────
_jira_attempt_counts = {}

def reset_jira_errors():
    global _jira_attempt_counts
    _jira_attempt_counts = {}

# ─── Tool: Create Account ─────────────────────────────────────────────────────
def create_account(system: str, employee_id: str) -> dict:
    """Create an account in an enterprise system for a new employee."""
    global _jira_attempt_counts

    if system not in SYSTEMS:
        return {"success": False, "error": f"Unknown system '{system}'. Valid: {SYSTEMS}"}

    employee = EMPLOYEES_DB.get(employee_id)
    if not employee:
        return {"success": False, "error": f"Employee {employee_id} not found in HR database"}

    # JIRA fails on first attempt — demonstrates error recovery
    if system == "jira":
        count = _jira_attempt_counts.get(employee_id, 0)
        _jira_attempt_counts[employee_id] = count + 1
        if count == 0:
            return {
                "success": False,
                "error": "JIRA API Error 503: Service Unavailable. The JIRA provisioning service is temporarily down.",
                "system": "jira",
                "retry_recommended": True,
            }

    username = employee["email"].split("@")[0]
    return {
        "success": True,
        "system": system,
        "account_id": f"{system.upper()}-{employee_id}-{random.randint(1000,9999)}",
        "username": username,
        "email": employee["email"],
        "role_assigned": employee["role"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# ─── Tool: Assign Buddy ───────────────────────────────────────────────────────
def assign_buddy(new_employee_id: str, buddy_id: str) -> dict:
    """Assign an onboarding buddy to a new employee."""
    new_emp = EMPLOYEES_DB.get(new_employee_id)
    buddy = EMPLOYEES_DB.get(buddy_id)

    if not new_emp:
        return {"success": False, "error": f"New employee {new_employee_id} not found"}
    if not buddy:
        return {"success": False, "error": f"Buddy {buddy_id} not found"}

    return {
        "success": True,
        "new_employee": new_emp["name"],
        "buddy_name": buddy["name"],
        "buddy_email": buddy["email"],
        "buddy_dept": buddy["dept"],
        "notification_sent": True,
        "message": f"{buddy['name']} has been notified and will schedule a 1:1 with {new_emp['name']} today.",
    }

# ─── Tool: Schedule Meeting ───────────────────────────────────────────────────
def schedule_meeting(attendee_ids: list, title: str, agenda: str = "") -> dict:
    """Schedule a calendar meeting for a list of employees."""
    attendees = []
    missing = []
    for eid in attendee_ids:
        emp = EMPLOYEES_DB.get(eid)
        if emp:
            attendees.append({"id": eid, "name": emp["name"], "email": emp["email"]})
        else:
            missing.append(eid)

    if not attendees:
        return {"success": False, "error": "No valid attendees found"}

    start_dt = datetime.now() + timedelta(days=1, hours=10)
    return {
        "success": True,
        "meeting_id": f"MTG-{random.randint(10000, 99999)}",
        "title": title,
        "attendees": [a["name"] for a in attendees],
        "attendee_emails": [a["email"] for a in attendees],
        "start_time": start_dt.strftime("%Y-%m-%d %H:%M"),
        "duration_mins": 60,
        "agenda": agenda or "See meeting title",
        "calendar_link": f"https://calendar.google.com/event/tc{random.randint(100000,999999)}",
        "invites_sent": True,
    }

# ─── Tool: Send Email ─────────────────────────────────────────────────────────
def send_email(to_employee_ids: list, subject: str, body: str) -> dict:
    """Send an email to one or more employees."""
    recipients = []
    for eid in to_employee_ids:
        emp = EMPLOYEES_DB.get(eid)
        if emp:
            recipients.append({"name": emp["name"], "email": emp["email"]})

    if not recipients:
        return {"success": False, "error": "No valid recipients found"}

    return {
        "success": True,
        "message_id": f"MSG-{random.randint(100000,999999)}",
        "to": [r["email"] for r in recipients],
        "to_names": [r["name"] for r in recipients],
        "subject": subject,
        "preview": body[:120] + "..." if len(body) > 120 else body,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "delivered",
    }

# ─── Tool: Create JIRA Ticket ─────────────────────────────────────────────────
def create_jira_ticket(project: str, title: str, description: str, assignee_id: str, priority: str = "Medium", labels: list = None) -> dict:
    """Create a JIRA task/ticket and assign it to an employee."""
    emp = EMPLOYEES_DB.get(assignee_id)
    assignee_name = emp["name"] if emp else assignee_id
    ticket_num = random.randint(100, 999)

    return {
        "success": True,
        "ticket_id": f"{project}-{ticket_num}",
        "title": title,
        "assignee": assignee_name,
        "assignee_email": emp["email"] if emp else None,
        "priority": priority,
        "labels": labels or [],
        "status": "Open",
        "url": f"https://techcorp.atlassian.net/browse/{project}-{ticket_num}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# ─── Tool: Get Meeting Transcript ─────────────────────────────────────────────
def get_meeting_transcript(meeting_id: str) -> dict:
    """Retrieve a meeting transcript from the meeting intelligence system."""
    transcript = MEETING_TRANSCRIPTS.get(meeting_id)
    if not transcript:
        return {"success": False, "error": f"Meeting {meeting_id} not found"}
    return {"success": True, **transcript}

# ─── Tool: Flag Ambiguous Item ────────────────────────────────────────────────
def flag_ambiguous_item(item_description: str, reason: str, suggested_owners: list) -> dict:
    """Flag an action item as ambiguous when no clear owner can be determined."""
    return {
        "success": True,
        "flagged": True,
        "item": item_description,
        "reason": reason,
        "suggested_owners": suggested_owners,
        "status": "AWAITING_CLARIFICATION",
        "notification": "Flagged in meeting summary. Team lead notified to assign owner.",
        "flagged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# ─── Tool: Send Meeting Summary ───────────────────────────────────────────────
def send_meeting_summary(meeting_id: str, recipient_ids: list, summary: str, action_items: list) -> dict:
    """Send the meeting summary and action items to all participants."""
    recipients = []
    for eid in recipient_ids:
        emp = EMPLOYEES_DB.get(eid)
        if emp:
            recipients.append(emp["email"])

    return {
        "success": True,
        "meeting_id": meeting_id,
        "sent_to": recipients,
        "action_items_count": len(action_items),
        "summary_length": len(summary),
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Summary delivered to all participants",
    }

# ─── Tool: Check Approval Status ──────────────────────────────────────────────
def check_approval_status(request_id: str) -> dict:
    """Check the current status of a procurement or workflow approval request."""
    req = APPROVAL_REQUESTS.get(request_id)
    if not req:
        return {"success": False, "error": f"Request {request_id} not found"}

    approver = EMPLOYEES_DB.get(req["primary_approver"], {"name": "Unknown"})
    on_leave = req["primary_approver"] in EMPLOYEES_ON_LEAVE
    created = datetime.fromisoformat(req["created_at"])
    hours_pending = (datetime.now() - created).total_seconds() / 3600
    sla_remaining = req["sla_hours"] - hours_pending

    return {
        "success": True,
        "request_id": request_id,
        "title": req["title"],
        "amount": f"₹{req['amount']:,}",
        "status": req["status"],
        "primary_approver": approver.get("name"),
        "approver_on_leave": on_leave,
        "hours_pending": round(hours_pending, 1),
        "sla_hours": req["sla_hours"],
        "hours_until_breach": round(sla_remaining, 1),
        "sla_breached": sla_remaining < 0,
        "breach_risk": "CRITICAL" if sla_remaining < 0 else ("HIGH" if sla_remaining < 4 else "MEDIUM"),
    }

# ─── Tool: Find Delegate Approver ─────────────────────────────────────────────
def find_delegate_approver(request_id: str, original_approver_id: str) -> dict:
    """Find an available delegate approver when the primary approver is unavailable."""
    req = APPROVAL_REQUESTS.get(request_id)
    if not req:
        return {"success": False, "error": f"Request {request_id} not found"}

    original = EMPLOYEES_DB.get(original_approver_id, {})
    original_manager_id = original.get("manager")
    delegate = EMPLOYEES_DB.get(original_manager_id)

    if not delegate:
        return {"success": False, "error": "No eligible delegate found in approval hierarchy"}

    return {
        "success": True,
        "delegate_id": original_manager_id,
        "delegate_name": delegate["name"],
        "delegate_role": delegate["role"],
        "delegate_email": delegate["email"],
        "authority_basis": f"Manager of {original.get('name', original_approver_id)}",
    }

# ─── Tool: Reassign Approval ──────────────────────────────────────────────────
def reassign_approval(request_id: str, delegate_id: str, reason: str) -> dict:
    """Reassign a pending approval to a delegate and log the override in the audit trail."""
    req = APPROVAL_REQUESTS.get(request_id)
    if not req:
        return {"success": False, "error": f"Request {request_id} not found"}

    delegate = EMPLOYEES_DB.get(delegate_id)
    if not delegate:
        return {"success": False, "error": f"Delegate {delegate_id} not found"}

    original = EMPLOYEES_DB.get(req["primary_approver"], {"name": "Unknown"})

    APPROVAL_REQUESTS[request_id]["status"] = "reassigned_to_delegate"
    APPROVAL_REQUESTS[request_id]["current_approver"] = delegate_id

    return {
        "success": True,
        "request_id": request_id,
        "original_approver": original.get("name"),
        "new_approver": delegate["name"],
        "new_approver_email": delegate["email"],
        "reason": reason,
        "reassigned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "audit_log": f"[OVERRIDE] Approval for '{req['title']}' reassigned from {original.get('name')} (on leave) to {delegate['name']} ({delegate['role']}). Reason: {reason}",
        "sla_recovery": "SLA breach avoided. Delegate notified with 2-hour response SLA.",
    }

# ─── Tool: Log SLA Override ───────────────────────────────────────────────────
def log_sla_override(request_id: str, action: str, agent_reasoning: str) -> dict:
    """Log an SLA override action with full audit trail for compliance."""
    return {
        "success": True,
        "log_id": f"SLA-LOG-{random.randint(10000,99999)}",
        "request_id": request_id,
        "action": action,
        "agent_reasoning": agent_reasoning,
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "compliance_record": "Logged in SOX-compliant audit database",
        "retention_period": "7 years",
    }

# ─── Tool: Get Employee Info ──────────────────────────────────────────────────
def get_employee_info(employee_id: str) -> dict:
    """Get details about an employee from the HR database."""
    emp = EMPLOYEES_DB.get(employee_id)
    if not emp:
        return {"success": False, "error": f"Employee {employee_id} not found"}
    return {"success": True, "employee_id": employee_id, **emp}

# ─── Tool: Escalate to IT ─────────────────────────────────────────────────────
def escalate_to_it(issue: str, employee_id: str, priority: str = "High") -> dict:
    """Escalate a technical issue to the IT support team."""
    emp = EMPLOYEES_DB.get(employee_id, {"name": employee_id})
    it_admin = EMPLOYEES_DB.get("EMP005")

    return {
        "success": True,
        "ticket_id": f"IT-{random.randint(1000,9999)}",
        "issue": issue,
        "affected_employee": emp.get("name", employee_id),
        "assigned_to": it_admin["name"] if it_admin else "IT Support",
        "priority": priority,
        "expected_resolution": "Within 2 business hours",
        "escalated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# ─── Master Tool Dispatcher ───────────────────────────────────────────────────
TOOL_MAP = {
    "create_account": create_account,
    "assign_buddy": assign_buddy,
    "schedule_meeting": schedule_meeting,
    "send_email": send_email,
    "create_jira_ticket": create_jira_ticket,
    "get_meeting_transcript": get_meeting_transcript,
    "flag_ambiguous_item": flag_ambiguous_item,
    "send_meeting_summary": send_meeting_summary,
    "check_approval_status": check_approval_status,
    "find_delegate_approver": find_delegate_approver,
    "reassign_approval": reassign_approval,
    "log_sla_override": log_sla_override,
    "get_employee_info": get_employee_info,
    "escalate_to_it": escalate_to_it,
}

def execute_tool(name: str, inputs: dict) -> dict:
    fn = TOOL_MAP.get(name)
    if not fn:
        return {"success": False, "error": f"Unknown tool: {name}"}
    try:
        return fn(**inputs)
    except Exception as e:
        return {"success": False, "error": str(e)}
