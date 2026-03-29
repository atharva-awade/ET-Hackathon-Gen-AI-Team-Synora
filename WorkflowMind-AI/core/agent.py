"""
WorkflowMind AI — Multi-Agent Runner
Uses NVIDIA NIM API (OpenAI-compatible) with function calling for genuine agentic reasoning.
Model: meta/llama-3.1-70b-instruct (free tier via build.nvidia.com)
Each agent has a distinct role, system prompt, and tool set.
API Key: obtain free key at https://build.nvidia.com
"""
import json
import os
import time
from datetime import datetime
from typing import Generator
from openai import OpenAI
from core.tools import execute_tool, reset_jira_errors

# ─── Agent Role Definitions ───────────────────────────────────────────────────

AGENT_ICONS = {
    "Orchestrator":  "🎯",
    "Retrieval":     "🔍",
    "Execution":     "⚡",
    "Decision":      "🧠",
    "Verification":  "✅",
    "ErrorRecovery": "🔄",
    "Audit":         "📋",
}

# ─── Tool Schemas (OpenAI / NVIDIA format) ────────────────────────────────────

ALL_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_account",
            "description": "Create an account in an enterprise system (github, slack, jira, hr_portal, gsuite) for a new employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system": {"type": "string", "description": "System name: github, slack, jira, hr_portal, or gsuite"},
                    "employee_id": {"type": "string", "description": "Employee ID, e.g. NEW001"},
                },
                "required": ["system", "employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "assign_buddy",
            "description": "Assign an onboarding buddy to a new employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_employee_id": {"type": "string"},
                    "buddy_id": {"type": "string", "description": "Employee ID of the buddy, e.g. EMP001"},
                },
                "required": ["new_employee_id", "buddy_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Schedule a calendar meeting with a list of employees.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attendee_ids": {"type": "array", "items": {"type": "string"}},
                    "title": {"type": "string"},
                    "agenda": {"type": "string"},
                },
                "required": ["attendee_ids", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to one or more employees.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_employee_ids": {"type": "array", "items": {"type": "string"}},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to_employee_ids", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_jira_ticket",
            "description": "Create a JIRA task and assign it to an employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "JIRA project key, e.g. ENG"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "assignee_id": {"type": "string"},
                    "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
                    "labels": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["project", "title", "description", "assignee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_meeting_transcript",
            "description": "Retrieve a meeting transcript from the system.",
            "parameters": {
                "type": "object",
                "properties": {"meeting_id": {"type": "string"}},
                "required": ["meeting_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_ambiguous_item",
            "description": "Flag an action item as ambiguous when no clear owner can be determined.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_description": {"type": "string"},
                    "reason": {"type": "string"},
                    "suggested_owners": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["item_description", "reason", "suggested_owners"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_meeting_summary",
            "description": "Send the processed meeting summary and action items to all participants.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {"type": "string"},
                    "recipient_ids": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                    "action_items": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["meeting_id", "recipient_ids", "summary", "action_items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_approval_status",
            "description": "Check the status of a procurement or workflow approval request.",
            "parameters": {
                "type": "object",
                "properties": {"request_id": {"type": "string"}},
                "required": ["request_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_delegate_approver",
            "description": "Find an available delegate approver when the primary approver is on leave.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "original_approver_id": {"type": "string"},
                },
                "required": ["request_id", "original_approver_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reassign_approval",
            "description": "Reassign a pending approval to a delegate and log the override with audit trail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "delegate_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["request_id", "delegate_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_sla_override",
            "description": "Log an SLA override action in the compliance audit database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "action": {"type": "string"},
                    "agent_reasoning": {"type": "string"},
                },
                "required": ["request_id", "action", "agent_reasoning"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_info",
            "description": "Look up an employee's details from the HR database.",
            "parameters": {
                "type": "object",
                "properties": {"employee_id": {"type": "string"}},
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_it",
            "description": "Escalate a technical system issue to the IT support team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string"},
                    "employee_id": {"type": "string"},
                    "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
                },
                "required": ["issue", "employee_id"],
            },
        },
    },
]

TOOL_SCHEMA_MAP = {t["function"]["name"]: t for t in ALL_TOOL_SCHEMAS}


# ─── Step Event (yielded to UI) ───────────────────────────────────────────────

class StepEvent:
    def __init__(self, agent: str, action: str, details: dict, status: str = "success",
                 error: bool = False, recovery: bool = False):
        self.agent = agent
        self.action = action
        self.details = details
        self.status = status
        self.error = error
        self.recovery = recovery
        self.timestamp = datetime.now().strftime("%H:%M:%S")
        self.icon = AGENT_ICONS.get(agent, "🤖")

    def to_audit_row(self):
        return {
            "timestamp": self.timestamp,
            "agent": self.agent,
            "action": self.action,
            "status": self.status,
            "details": json.dumps(self.details, ensure_ascii=False)[:200],
        }


# ─── Core Agent Runner ────────────────────────────────────────────────────────

class AgentRunner:
    """
    Multi-agent system using NVIDIA NIM API (OpenAI-compatible) with function calling.
    Model: meta/llama-3.1-70b-instruct (free tier — get key at build.nvidia.com)
    Each agent role gets a distinct system prompt and tool subset.
    """

    def __init__(self, api_key: str, model: str = "meta/llama-3.1-70b-instruct"):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )
        self.model = model
        self.audit_trail = []

    def _get_tools(self, tool_names: list) -> list:
        return [TOOL_SCHEMA_MAP[n] for n in tool_names if n in TOOL_SCHEMA_MAP]

    def _run_agent(
        self,
        agent_name: str,
        system_prompt: str,
        initial_message: str,
        tool_names: list,
        context: dict = None,
        max_iterations: int = 12,
    ) -> Generator[StepEvent, None, str]:
        """
        Run a single agent in a tool-use loop using NVIDIA API.
        Yields StepEvents and returns the final text response.
        """
        tools = self._get_tools(tool_names)
        user_content = initial_message
        if context:
            user_content += f"\n\nContext:\n{json.dumps(context, indent=2, ensure_ascii=False)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        for iteration in range(max_iterations):
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 2048,
                "temperature": 0.2,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
                kwargs["parallel_tool_calls"] = False  # Llama only supports single tool-calls

            # ── API call with rate-limit retry ───────────────────────────
            response = None
            for attempt in range(3):
                try:
                    response = self.client.chat.completions.create(**kwargs)
                    break
                except Exception as exc:
                    err_str = str(exc)
                    if "429" in err_str or "rate" in err_str.lower():
                        wait = 20 * (attempt + 1)
                        yield StepEvent(
                            agent=agent_name,
                            action=f"Rate limit reached — pausing {wait}s before retry ({attempt+1}/3)…",
                            details={},
                            status="recovery",
                            recovery=True,
                        )
                        time.sleep(wait)
                        if attempt == 2:
                            raise
                    else:
                        raise
            if response is None:
                break
            msg = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            # No tool calls — agent is done
            if finish_reason == "stop" or not msg.tool_calls:
                final_text = msg.content or "Agent task complete."
                yield StepEvent(
                    agent=agent_name,
                    action="Completed analysis",
                    details={"summary": final_text[:300]},
                    status="complete",
                )
                return final_text

            # Process tool calls
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]})

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_input = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_input = {}

                result = execute_tool(tool_name, tool_input)
                is_error = not result.get("success", True)
                is_recovery = is_error and result.get("retry_recommended", False)

                event = StepEvent(
                    agent=agent_name,
                    action=f"Called `{tool_name}`",
                    details={"input": tool_input, "result": result},
                    status="error" if is_error else "success",
                    error=is_error,
                    recovery=is_recovery,
                )
                self.audit_trail.append(event.to_audit_row())
                yield event

                # Feed tool result back
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        return "Max iterations reached"

    # ── Scenario 1: Employee Onboarding ──────────────────────────────────────

    def run_onboarding(self, employee_id: str = "NEW001") -> Generator[StepEvent, None, None]:
        reset_jira_errors()
        self.audit_trail = []

        yield StepEvent("Orchestrator", "Initialising onboarding workflow",
                        {"employee_id": employee_id,
                         "systems": ["github", "slack", "jira", "hr_portal", "gsuite"],
                         "steps": ["Account creation", "Buddy assignment", "Scheduling", "Welcome email"]},
                        status="planning")
        time.sleep(0.3)

        # Agent 1 — Retrieval
        yield StepEvent("Retrieval", "Fetching new employee details from HR database",
                        {"employee_id": employee_id}, status="running")
        for event in self._run_agent(
            "Retrieval",
            "You are the Retrieval Agent in an enterprise onboarding system. Look up employee information using get_employee_info.",
            f"Look up details for new employee {employee_id} who is joining today.",
            ["get_employee_info"],
        ):
            yield event
        time.sleep(0.2)

        # Agent 2 — Execution: Create all accounts
        yield StepEvent("Execution", "Creating accounts across all 5 enterprise systems",
                        {"systems": ["github", "slack", "jira", "hr_portal", "gsuite"]}, status="running")
        for event in self._run_agent(
            "Execution",
            """You are the Execution Agent in an enterprise onboarding multi-agent system.
Create accounts for the new employee across ALL 5 required systems: github, slack, jira, hr_portal, gsuite.
IMPORTANT: If a system returns an error (like JIRA returning 503), retry it ONCE using create_account again.
If retry also fails, use escalate_to_it to escalate to IT support.
You MUST attempt all 5 systems. Do not stop until all are done.""",
            f"Create accounts for employee {employee_id} across all 5 systems: github, slack, jira, hr_portal, gsuite.",
            ["create_account", "escalate_to_it"],
        ):
            if event.error and "jira" in str(event.details).lower():
                event.recovery = True
                event.action = "JIRA 503 Error — triggering automatic retry"
            yield event
        time.sleep(0.2)

        # Agent 3 — Execution: Buddy + Meetings
        yield StepEvent("Execution", "Assigning buddy and scheduling orientation meetings",
                        {"buddy": "EMP001 (Arjun Sharma)", "manager": "EMP003"}, status="running")
        for event in self._run_agent(
            "Execution",
            """You are the Coordination Agent in an enterprise onboarding system.
Do all 3 tasks:
1. Assign buddy EMP001 (Arjun Sharma) to the new employee NEW001
2. Schedule an orientation meeting: attendees NEW001 and EMP003 (manager), title "Orientation — Ananya Gupta"
3. Schedule a team welcome meeting: attendees EMP001, EMP003, NEW001, title "Team Welcome — Ananya Gupta"
Complete all three.""",
            f"New employee {employee_id} needs buddy assignment and two meetings scheduled.",
            ["assign_buddy", "schedule_meeting", "get_employee_info"],
        ):
            yield event
        time.sleep(0.2)

        # Agent 4 — Communication: Welcome email
        yield StepEvent("Execution", "Composing and sending personalised welcome email",
                        {"recipient": "NEW001 — Ananya Gupta"}, status="running")
        for event in self._run_agent(
            "Execution",
            """You are the Communication Agent. Send a warm welcome email to the new employee.
The email should mention: their role (Backend Engineer), buddy's name (Arjun Sharma),
orientation meeting scheduled for tomorrow, and that accounts have been set up across GitHub, Slack, JIRA, HR Portal, and GSuite.
Send to employee NEW001.""",
            f"Send a comprehensive welcome email to new employee {employee_id} (Ananya Gupta, Backend Engineer).",
            ["send_email"],
        ):
            yield event
        time.sleep(0.2)

        # Agent 5 — Verification
        yield StepEvent("Verification", "Verifying all onboarding tasks completed successfully",
                        {"checklist": ["5 accounts", "buddy", "meetings", "email"]}, status="running")
        for event in self._run_agent(
            "Verification",
            "You are the Verification Agent. Confirm the onboarding is complete. Summarise all completed steps: accounts provisioned, buddy assigned, meetings scheduled, email sent.",
            f"Verify the onboarding for employee {employee_id} (Ananya Gupta) is complete.",
            [],
        ):
            yield event

        yield StepEvent("Audit", "Onboarding workflow completed — audit trail saved",
                        {"employee": "Ananya Gupta (NEW001)", "status": "COMPLETED",
                         "total_steps": len(self.audit_trail), "sla_met": True},
                        status="complete")

    # ── Scenario 2: Meeting Intelligence ─────────────────────────────────────

    def run_meeting_intelligence(self, meeting_id: str = "MTG-SPRINT-42") -> Generator[StepEvent, None, None]:
        self.audit_trail = []

        yield StepEvent("Orchestrator", "Initialising meeting intelligence pipeline",
                        {"meeting_id": meeting_id,
                         "steps": ["Transcript retrieval", "Action extraction", "JIRA creation", "Summary dispatch"]},
                        status="planning")
        time.sleep(0.3)

        # Agent 1 — Retrieval
        yield StepEvent("Retrieval", f"Fetching transcript for {meeting_id}", {"meeting_id": meeting_id}, status="running")
        for event in self._run_agent(
            "Retrieval",
            "You are the Retrieval Agent. Retrieve the meeting transcript using get_meeting_transcript.",
            f"Retrieve the transcript for meeting {meeting_id}.",
            ["get_meeting_transcript"],
        ):
            yield event
        time.sleep(0.2)

        # Agent 2 — Decision + JIRA
        yield StepEvent("Decision", "Extracting action items, assigning owners, creating JIRA tickets",
                        {"participants": 4, "project": "SPRINT"}, status="running")
        for event in self._run_agent(
            "Decision",
            """You are the Decision Agent in a meeting intelligence system.
The meeting transcript for MTG-SPRINT-42 is a sprint planning meeting with these participants:
- Arjun Sharma (EMP001) — Senior Engineer
- Priya Patel (EMP002) — Product Manager
- Rahul Verma (EMP003) — Engineering Manager
- Ananya Gupta (NEW001) — New Backend Engineer

Action items from the transcript:
1. Arjun: Finish payment gateway retry logic and unit tests — by Wednesday (JIRA: ENG project, High priority)
2. Arjun + Ananya: Implement new user onboarding flow from Priya's wireframes (JIRA: ENG, High)
3. Ananya: Sync with Arjun on payment retry logic today (JIRA: ENG, Medium)
4. Priya: Coordinate security review before payment feature goes live (JIRA: ENG, High)
5. Arjun: Investigate and fix Android 12 crash — CRITICAL (JIRA: ENG, Critical)
6. Analytics dashboard ownership — AMBIGUOUS: nobody clearly owns this. Flag it!

For item 6 (analytics dashboard), use flag_ambiguous_item because no clear owner was assigned.
Create JIRA tickets for items 1-5, then flag item 6 as ambiguous.""",
            f"Process all action items from the sprint planning meeting {meeting_id}.",
            ["create_jira_ticket", "flag_ambiguous_item"],
        ):
            yield event
        time.sleep(0.2)

        # Agent 3 — Send summary
        yield StepEvent("Execution", "Sending meeting summary to all participants",
                        {"recipients": ["EMP001", "EMP002", "EMP003", "NEW001"]}, status="running")
        for event in self._run_agent(
            "Execution",
            """You are the Communication Agent. Send a meeting summary for MTG-SPRINT-42 to all 4 participants.
Recipients: EMP001, EMP002, EMP003, NEW001
The summary should include key decisions and that JIRA tickets have been created.
Note: Analytics dashboard ownership was flagged as ambiguous and needs team clarification.""",
            f"Send the complete meeting summary for {meeting_id} to all participants.",
            ["send_meeting_summary", "send_email"],
        ):
            yield event
        time.sleep(0.2)

        # Agent 4 — Verification
        yield StepEvent("Verification", "Verifying all action items processed and notifications sent", {}, status="running")
        for event in self._run_agent(
            "Verification",
            "You are the Verification Agent. Confirm: JIRA tickets created for all clear items, ambiguous item flagged, summary sent to all participants.",
            f"Verify meeting {meeting_id} processing is complete.",
            [],
        ):
            yield event

        yield StepEvent("Audit", "Meeting intelligence pipeline completed — all actions tracked",
                        {"meeting_id": meeting_id, "status": "COMPLETED",
                         "jira_tickets": 5, "ambiguous_items": 1}, status="complete")

    # ── Scenario 3: SLA Breach Prevention ────────────────────────────────────

    def run_sla_breach(self, request_id: str = "PR-2847") -> Generator[StepEvent, None, None]:
        self.audit_trail = []

        yield StepEvent("Orchestrator", "SLA breach alert triggered — initiating autonomous response",
                        {"request_id": request_id, "alert": "Approval stuck > 48 hours — SLA breached",
                         "steps": ["Status check", "Bottleneck diagnosis", "Delegation", "Audit log", "Notifications"]},
                        status="planning")
        time.sleep(0.3)

        # Agent 1 — Retrieval
        yield StepEvent("Retrieval", f"Checking approval status for {request_id}", {"request_id": request_id}, status="running")
        for event in self._run_agent(
            "Retrieval",
            "You are the Retrieval Agent in a workflow monitoring system. Check approval request status using check_approval_status.",
            f"Check the current status of approval request {request_id} and assess SLA breach risk.",
            ["check_approval_status"],
        ):
            yield event
        time.sleep(0.2)

        # Agent 2 — Decision: Diagnose + find delegate
        yield StepEvent("Decision", "Diagnosing bottleneck — primary approver on leave",
                        {"primary_approver": "EMP006 (VP Product)", "status": "ON LEAVE"}, status="running")
        for event in self._run_agent(
            "Decision",
            """You are the Decision Agent in a workflow monitoring system.
The approval request PR-2847 has been pending for 49 hours. The SLA was 24 hours — it is ALREADY BREACHED.
The primary approver is EMP006 (Deepak Menon, VP Product) who is on leave.
1. First check the approval status using check_approval_status for PR-2847
2. Find a delegate using find_delegate_approver with request_id=PR-2847 and original_approver_id=EMP006
3. Look up the delegate's info using get_employee_info""",
            f"Request {request_id} has breached SLA. Primary approver EMP006 is on leave. Find a delegate.",
            ["check_approval_status", "find_delegate_approver", "get_employee_info"],
        ):
            yield event
        time.sleep(0.2)

        # Agent 3 — Execution: Reassign + notify
        yield StepEvent("Execution", "Reassigning approval to delegate — CTO (EMP007)",
                        {"from": "EMP006 (on leave)", "to": "EMP007 (CTO)"}, status="running")
        for event in self._run_agent(
            "Execution",
            """You are the Execution Agent in a workflow monitoring system.
Execute the SLA recovery for PR-2847:
1. Reassign the approval: request_id=PR-2847, delegate_id=EMP007, reason="Primary approver EMP006 (Deepak Menon) is on leave. SLA breached by 25 hours. Escalating to manager per approval policy."
2. Log the SLA override: request_id=PR-2847, action="Approval reassigned to delegate CTO", agent_reasoning="SLA already exceeded by 25 hours. Primary approver on leave. Delegated to EMP007 per approval escalation matrix."
3. Send email to EMP007 (delegate) notifying them of the urgent approval needed
4. Send email to EMP002 (requestor Priya Patel) that the approval has been reassigned
Do all 4 steps.""",
            f"Execute full SLA recovery for {request_id}.",
            ["reassign_approval", "log_sla_override", "send_email"],
        ):
            yield event
        time.sleep(0.2)

        # Agent 4 — Verification
        yield StepEvent("Verification", "Verifying SLA recovery complete and audit trail in place", {}, status="running")
        for event in self._run_agent(
            "Verification",
            "You are the Verification Agent. Confirm: approval reassigned, audit log created, both parties notified. Provide compliance confirmation.",
            f"Confirm SLA breach recovery for {request_id} is complete.",
            [],
        ):
            yield event

        yield StepEvent("Audit", "SLA breach prevented — SOX-compliant audit trail recorded",
                        {"request_id": request_id, "breach_prevented": True,
                         "compliance": "SOX-compliant override logged", "audit_logged": True},
                        status="complete")
