"""
WorkflowMind AI — ET AI Hackathon 2026
Track 2: Agentic AI for Autonomous Enterprise Workflows

Multi-agent system for autonomous enterprise workflow execution.
Built with: Llama 3.1 70B (NVIDIA NIM), OpenAI-compatible Tool Use, Streamlit
"""
import os
import time
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WorkflowMind AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* Global font excluding icons so Material ligatures process correctly */
    html, body, .stApp, p, h1, h2, h3, h4, h5, h6, li {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; 
    }
    div:not(.stIcon):not(.material-symbols-rounded):not([class*="icon"]), 
    span:not(.stIcon):not(.material-symbols-rounded):not([class*="icon"]) {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main background */
    .main { background: #06101e; }

    /* ── Hero Banner ── */
    .hero-banner {
        background: linear-gradient(135deg, #0d2444 0%, #080f1e 45%, #0f1e35 75%, #180c36 100%);
        border-radius: 20px;
        padding: 36px 44px;
        margin-bottom: 28px;
        border: 1px solid rgba(74, 144, 217, 0.22);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -60%; left: -20%;
        width: 140%; height: 200%;
        background:
            radial-gradient(ellipse at 30% 40%, rgba(74,144,217,0.08) 0%, transparent 55%),
            radial-gradient(ellipse at 75% 60%, rgba(138,43,226,0.05) 0%, transparent 50%);
        pointer-events: none;
    }
    .hero-title {
        font-size: 2.6rem !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        margin: 0 !important;
        letter-spacing: -1.5px !important;
        line-height: 1.1 !important;
    }
    .hero-sub {
        font-size: 0.97rem;
        color: #7a9bbf;
        margin-top: 8px;
        font-weight: 400;
        letter-spacing: 0.1px;
    }
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, #e55a24, #cc3d0a);
        color: white;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 4px 13px;
        border-radius: 20px;
        margin-right: 8px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .hero-badge-blue { background: linear-gradient(135deg, #1558a0, #0e3d72); }

    /* ── Agent Pipeline ── */
    .pipeline-container { display: flex; align-items: center; gap: 0; margin: 16px 0; }
    .agent-node {
        flex: 1;
        text-align: center;
        padding: 14px 8px;
        border-radius: 12px;
        border: 1.5px solid rgba(45,74,110,0.55);
        background: linear-gradient(135deg, #0c1620, #101827);
        color: #4a5e78;
        font-size: 0.75rem;
        font-weight: 600;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.2px;
    }
    .agent-node.active {
        background: linear-gradient(135deg, #142b52, #0c1e3d);
        border-color: #4A90D9;
        color: #FFFFFF;
        box-shadow: 0 0 22px rgba(74,144,217,0.5), 0 0 44px rgba(74,144,217,0.15);
        transform: translateY(-3px) scale(1.06);
    }
    .agent-node.complete {
        background: linear-gradient(135deg, #0a2010, #071508);
        border-color: #27ae60;
        color: #4db870;
        box-shadow: 0 0 10px rgba(39,174,96,0.25);
    }
    .agent-node.error {
        background: linear-gradient(135deg, #2a0c0c, #1a0808);
        border-color: #c0392b;
        color: #e05252;
        box-shadow: 0 0 10px rgba(192,57,43,0.25);
    }
    .arrow { 
        color: #557299; 
        font-size: 1.6rem; 
        font-weight: 800; 
        text-align: center; 
        margin-top: 18px; 
        text-shadow: 0 0 12px rgba(74,144,217,0.3);
    }

    /* ── Step Cards ── */
    .step-card {
        background: linear-gradient(135deg, #0b1520, #0f1c2e);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 8px;
        border: 1px solid rgba(40,65,95,0.5);
        border-left: 3px solid rgba(45,74,110,0.8);
        transition: border-color 0.2s ease, transform 0.15s ease;
    }
    .step-card:hover { border-color: rgba(74,144,217,0.35); transform: translateX(2px); }
    .step-card.success  { border-left-color: #27ae60; }
    .step-card.error    { border-left-color: #c0392b; background: linear-gradient(135deg, #140808, #1a0d0d); }
    .step-card.recovery { border-left-color: #e67e22; background: linear-gradient(135deg, #14100a, #1a140d); }
    .step-card.planning { border-left-color: #7c3aed; background: linear-gradient(135deg, #100e18, #130f1e); }
    .step-card.complete { border-left-color: #27ae60; background: linear-gradient(135deg, #08140a, #0c1a0d); }

    .agent-label   { color: #4A90D9; font-weight: 700; font-size: 0.8rem; }
    .human-message { color: #cddcee; font-weight: 500; font-size: 0.88rem; }

    /* ── Metric Cards ── */
    .metric-card {
        background: linear-gradient(135deg, #0b1520, #0f1c2e);
        border-radius: 14px;
        padding: 22px 18px;
        text-align: center;
        border: 1px solid rgba(40,65,95,0.5);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: rgba(74,144,217,0.4);
        transform: translateY(-3px);
        box-shadow: 0 8px 28px rgba(0,0,0,0.45);
    }
    .metric-value { font-size: 2.2rem; font-weight: 800; color: #4A90D9; letter-spacing: -1px; }
    .metric-label {
        font-size: 0.72rem; color: #4a5e78; margin-top: 6px;
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px;
    }

    /* ── Scenario Cards ── */
    .scenario-card {
        background: linear-gradient(135deg, #0b1520, #0f1c2e);
        border-radius: 14px;
        padding: 22px 24px;
        border: 1px solid rgba(40,65,95,0.5);
        margin-bottom: 18px;
        transition: all 0.3s ease;
    }
    .scenario-card:hover {
        border-color: rgba(74,144,217,0.5);
        box-shadow: 0 8px 32px rgba(74,144,217,0.08);
    }
    .scenario-title { font-weight: 700; font-size: 1.08rem; color: #dde8f5; letter-spacing: -0.3px; }
    .scenario-desc  { font-size: 0.84rem; color: #4a5e78; margin-top: 8px; line-height: 1.65; }
    .tag {
        display: inline-block;
        font-size: 0.68rem; font-weight: 600;
        padding: 3px 10px; border-radius: 6px;
        margin-right: 5px; margin-top: 10px; letter-spacing: 0.3px;
    }
    .tag-green  { background: rgba(39,174,96,0.12);  color: #4db870; border: 1px solid rgba(39,174,96,0.25); }
    .tag-blue   { background: rgba(74,144,217,0.12); color: #6aaee8; border: 1px solid rgba(74,144,217,0.25); }
    .tag-orange { background: rgba(230,126,34,0.12); color: #e67e22; border: 1px solid rgba(230,126,34,0.25); }
    .tag-red    { background: rgba(192,57,43,0.12);  color: #e05252; border: 1px solid rgba(192,57,43,0.25); }

    /* ── Audit ── */
    .audit-header {
        background: linear-gradient(135deg, #0d2444, #091830);
        color: white; font-weight: 700; padding: 10px 16px;
        border-radius: 8px 8px 0 0; font-size: 0.9rem;
    }
    .badge-success { color: #4db870; font-weight: 700; }
    .badge-error   { color: #e05252; font-weight: 700; }
    .badge-warn    { color: #e67e22; font-weight: 700; }
    .badge-info    { color: #6aaee8; font-weight: 700; }

    /* ── Streamlit overrides ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* Completely nuke any raw text ligatures (like _arrow_right) leaking into the expander button 
       by forcing font size to 0 on the container, but restoring it for the paragraph label. */
    .stExpander div[role="button"], .stExpander summary { 
        font-size: 0px !important; 
        color: transparent !important; 
        padding-bottom: 8px;
    }
    .stExpander div[role="button"] p, .stExpander summary p { 
        font-size: 0.85rem !important; 
        color: #8BA4BC !important; 
        margin: 0 !important;
        visibility: visible !important;
    }
    /* Hide the default Streamlit expander arrow containers natively */
    .stExpander summary svg,
    .stExpander div[data-testid="stExpanderToggleIcon"] { 
        display: none !important; 
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1558a0, #4A90D9) !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1a6bbd, #5a9fec) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(74,144,217,0.4) !important;
    }
    .stProgress > div > div { background: linear-gradient(90deg, #1558a0, #4A90D9); }
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ───────────────────────────────────────────────────────
if "steps" not in st.session_state:
    st.session_state.steps = []
if "audit_trail" not in st.session_state:
    st.session_state.audit_trail = []
if "running" not in st.session_state:
    st.session_state.running = False
if "completed" not in st.session_state:
    st.session_state.completed = False
if "active_agents" not in st.session_state:
    st.session_state.active_agents = set()
if "done_agents" not in st.session_state:
    st.session_state.done_agents = set()
if "error_agents" not in st.session_state:
    st.session_state.error_agents = set()
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")


# ─── API Key (auto-loaded from .env) ────────────────────────────────────────
# Key is stored in .env — no sidebar needed
if not st.session_state.api_key:
    st.error("NVIDIA_API_KEY not found. Please add it to your .env file.")


# ─── Hero Banner ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
            <p class="hero-title" style="font-size:2.6rem !important; font-weight:900 !important; color:#FFFFFF !important; margin:0 !important; letter-spacing:-1.5px !important;">&#129302; WorkflowMind AI</p>
            <p class="hero-sub">Autonomous Multi-Agent System for Enterprise Workflow Orchestration</p>
            <p class="hero-sub" style="margin-top:8px; font-size:0.82rem;">
                5+ autonomous steps &nbsp;&middot;&nbsp; Real-time error recovery &nbsp;&middot;&nbsp;
                Full audit trail &nbsp;&middot;&nbsp; Zero human intervention
            </p>
        </div>
        <div style="text-align:right; min-width:180px;">
            <p style="color:#4a5e78; font-size:0.72rem; margin:0; text-transform:uppercase; letter-spacing:0.6px;">Built by</p>
            <p style="color:#FFFFFF; font-weight:800; font-size:1.15rem; margin:6px 0 0 0; letter-spacing:-0.3px;">Team Synora</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Top Metrics ──────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
metrics = [
    ("6", "Specialized Agents"),
    ("5+", "Autonomous Steps"),
    ("3", "Live Scenarios"),
    ("100%", "Audit Coverage"),
    ("0", "Human Interventions"),
]
for col, (val, label) in zip([m1, m2, m3, m4, m5], metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Scenario Tabs ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🧑‍💼 Scenario 1: Employee Onboarding",
    "🗣️ Scenario 2: Meeting Intelligence",
    "🚨 Scenario 3: SLA Breach Prevention",
    "📋 Full Audit Trail",
])


def humanize_step(step: dict) -> str:
    """Convert raw step data into plain English anyone can understand."""
    action  = step.get("action", "")
    details = step.get("details") or {}
    status  = step.get("status", "")
    is_error = step.get("error", False)

    # ── Planning / complete stages ──────────────────────────────────────────
    if status == "planning":
        steps_list = details.get("steps", [])
        if steps_list:
            return "Planning workflow: " + " → ".join(steps_list)
        return action

    if status == "complete":
        summary = details.get("summary", "")
        if summary:
            clean = summary[:240].replace("\n", " ").strip()
            return clean + ("…" if len(summary) > 240 else "")
        return "Stage completed successfully ✓"

    inp    = details.get("input", {})
    result = details.get("result", {})

    # ── Tool-specific human messages ────────────────────────────────────────
    if "create_account" in action:
        system = inp.get("system", "system").upper()
        if is_error:
            return f"⚠️ {system} account creation failed — service temporarily unavailable. Initiating automatic retry…"
        return f"Created {system} account → username: {result.get('username', '✓')}"

    if "assign_buddy" in action:
        buddy   = result.get("buddy_name", inp.get("buddy_id", "buddy"))
        new_emp = result.get("new_employee", inp.get("new_employee_id", "new employee"))
        return f"Assigned {buddy} as onboarding buddy for {new_emp}" + (" — they've been notified 📩" if result.get("notification_sent") else "")

    if "schedule_meeting" in action:
        title    = inp.get("title", "meeting")
        attendees = result.get("attendees", [])
        start    = result.get("start_time", "")
        n = len(attendees)
        return f"Scheduled '{title}' — {n} attendee{'s' if n!=1 else ''}" + (f", starting {start}" if start else "")

    if "send_email" in action:
        to_names = result.get("to_names", [])
        subject  = inp.get("subject", "")
        recipients = ", ".join(to_names[:2]) + (f" +{len(to_names)-2} more" if len(to_names) > 2 else "") if to_names else str(inp.get("to_employee_ids", ""))
        return f"Sent email to {recipients} 📧 — \"{subject[:60]}\""

    if "create_jira_ticket" in action:
        title     = result.get("title", inp.get("title", "ticket"))
        ticket_id = result.get("ticket_id", "")
        assignee  = result.get("assignee", inp.get("assignee_id", ""))
        priority  = inp.get("priority", "Medium")
        prefix = f"[{ticket_id}] " if ticket_id else ""
        return f"Created JIRA ticket {prefix}'{title[:55]}' → {assignee} ({priority} priority)"

    if "get_meeting_transcript" in action:
        title = result.get("title", inp.get("meeting_id", "meeting"))
        parts = result.get("participants", [])
        return f"Retrieved meeting transcript: '{title}'" + (f" — {len(parts)} participants" if parts else "")

    if "flag_ambiguous_item" in action:
        item   = inp.get("item_description", "item")
        reason = inp.get("reason", "")
        return f"🚩 Flagged for human review: '{item[:65]}'" + (f" — {reason[:50]}" if reason else "")

    if "send_meeting_summary" in action:
        count   = result.get("action_items_count", len(inp.get("action_items", [])))
        sent_to = result.get("sent_to", [])
        return f"Meeting summary with {count} action item{'s' if count!=1 else ''} sent to {len(sent_to)} participants 📨"

    if "check_approval_status" in action:
        hours   = result.get("hours_pending", 0)
        breached = result.get("sla_breached", False)
        title   = result.get("title", inp.get("request_id", ""))
        amount  = result.get("amount", "")
        risk_str = "⛔ SLA ALREADY BREACHED" if breached else ("⚠️ SLA at risk" if result.get("breach_risk") == "HIGH" else "✅ Within SLA")
        return f"Approval check: '{title}'" + (f" ({amount})" if amount else "") + f" — pending {hours:.0f}h — {risk_str}"

    if "find_delegate_approver" in action:
        name = result.get("delegate_name", "")
        role = result.get("delegate_role", "")
        if is_error:
            return "⚠️ Could not find a suitable delegate in the approval hierarchy"
        return f"Found available delegate: {name} ({role}) — authority confirmed ✓"

    if "reassign_approval" in action:
        new_app = result.get("new_approver", inp.get("delegate_id", "delegate"))
        req_id  = inp.get("request_id", "")
        orig    = result.get("original_approver", "previous approver")
        return f"Approval {req_id} reassigned: {orig} → {new_app} — both parties notified 🔀"

    if "log_sla_override" in action:
        log_id    = result.get("log_id", "")
        retention = result.get("retention_period", "7 years")
        return f"SOX-compliant override audit record created [{log_id}] — retained for {retention} 📂"

    if "get_employee_info" in action:
        name = result.get("name", inp.get("employee_id", ""))
        role = result.get("role", "")
        dept = result.get("dept", "")
        on_leave = inp.get("employee_id", "") in ["EMP006"]
        return f"Employee profile: {name} — {role}, {dept}" + (" 🏖️ (Currently on leave)" if on_leave else "")

    if "escalate_to_it" in action:
        ticket   = result.get("ticket_id", "")
        assigned = result.get("assigned_to", "IT Support")
        eta      = result.get("expected_resolution", "within 2 hours")
        priority = inp.get("priority", "High")
        return f"IT escalation raised [{ticket}] → {assigned} ({priority} priority) — expected resolution: {eta} 🛠️"

    return action  # fallback


def render_step(step: dict):
    css      = step.get("css_class", "")
    icon     = step.get("icon", "🤖")
    agent    = step.get("agent", "")
    action   = step.get("action", "")
    ts       = step.get("timestamp", "")
    is_error = step.get("error", False)
    is_rec   = step.get("recovery", False)
    status   = step.get("status", "")

    if is_error and not is_rec:
        status_icon = "❌"
    elif is_rec:
        status_icon = "🔄"
    elif status in ("complete", "success"):
        status_icon = "✅"
    elif status == "planning":
        status_icon = "🗺️"
    else:
        status_icon = "ℹ️"

    human_msg = humanize_step(step)

    st.markdown(f"""
    <div class="step-card {css}">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="flex:1; min-width:0;">
                <span class="agent-label">{icon} {agent}</span>
                <span style="color:#2d4a6e; margin:0 7px;">│</span>
                <span class="human-message">{human_msg}</span>
                &nbsp;{status_icon}
            </div>
            <span style="color:#2d4a6e; font-size:0.72rem; white-space:nowrap; margin-left:12px;">{ts}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # Show technical details in a collapsible expander (for engineers)
    details = step.get("details") or {}
    if isinstance(details, dict) and "input" in details:
        tool_name = action.replace("Called `", "").replace("`", "").strip()
        with st.expander(f"⚙️ Technical details — `{tool_name}`", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.caption("📥 Input Parameters")
                st.json(details.get("input", {}))
            with c2:
                st.caption("📤 Tool Response")
                st.json(details.get("result", {}))


def render_agent_pipeline(active: set, done: set, errors: set):
    agents = ["Orchestrator", "Retrieval", "Execution", "Verification", "ErrorRecovery", "Audit"]
    icons = {"Orchestrator": "🎯", "Retrieval": "🔍", "Execution": "⚡",
             "Verification": "✅", "ErrorRecovery": "🔄", "Audit": "📋"}
    cols = st.columns(len(agents) * 2 - 1)
    for i, agent in enumerate(agents):
        css_class = "active" if agent in active else ("complete" if agent in done else ("error" if agent in errors else ""))
        with cols[i * 2]:
            st.markdown(f"""
            <div class="agent-node {css_class}">
                {icons[agent]}<br>{agent}
            </div>""", unsafe_allow_html=True)
        if i < len(agents) - 1:
            with cols[i * 2 + 1]:
                st.markdown('<div class="arrow">→</div>', unsafe_allow_html=True)




def run_scenario(scenario_fn_name: str):
    if not st.session_state.api_key:
        st.error("NVIDIA_API_KEY not found. Please add it to your .env file.")
        return

    from core.agent import AgentRunner, AGENT_ICONS

    st.session_state.steps = []
    st.session_state.audit_trail = []
    st.session_state.running = True
    st.session_state.completed = False
    st.session_state.active_agents = set()
    st.session_state.done_agents = set()
    st.session_state.error_agents = set()

    runner = AgentRunner(api_key=st.session_state.api_key)
    scenario_map = {
        "onboarding": runner.run_onboarding,
        "meeting": runner.run_meeting_intelligence,
        "sla_breach": runner.run_sla_breach,
    }
    scenario_fn = scenario_map[scenario_fn_name]

    pipeline_placeholder = st.empty()
    steps_placeholder = st.empty()
    status_placeholder = st.empty()

    step_display = []
    current_agent = None

    try:
        for event in scenario_fn():
            # Update active agents
            if current_agent and current_agent != event.agent:
                st.session_state.done_agents.add(current_agent)
                st.session_state.active_agents.discard(current_agent)

            current_agent = event.agent
            st.session_state.active_agents.add(event.agent)

            if event.error:
                st.session_state.error_agents.add(event.agent)
            if event.recovery:
                st.session_state.active_agents.add("ErrorRecovery")
                css = "recovery"
            elif event.error:
                css = "error"
            elif event.status in ("complete", "planning"):
                css = event.status
            else:
                css = "success" if not event.error else "error"

            step_entry = {
                "icon": event.icon,
                "agent": event.agent,
                "action": event.action,
                "details": event.details,
                "status": event.status,
                "error": event.error,
                "recovery": event.recovery,
                "css_class": css,
                "timestamp": event.timestamp,
            }
            step_display.append(step_entry)
            st.session_state.steps.append(step_entry)

            # Add to audit trail
            st.session_state.audit_trail.append(event.to_audit_row())

            # Update pipeline
            with pipeline_placeholder.container():
                render_agent_pipeline(
                    st.session_state.active_agents,
                    st.session_state.done_agents,
                    st.session_state.error_agents,
                )

            # Update step log
            with steps_placeholder.container():
                for s in step_display[-12:]:  # Show last 12 steps
                    render_step(s)

            # Status line
            with status_placeholder.container():
                if event.error:
                    st.warning(f"⚠️ {event.agent}: Error encountered — initiating recovery...")
                elif event.recovery:
                    st.info(f"🔄 {event.agent}: Retrying after error...")
                else:
                    st.info(f"🔄 Running: **{event.agent}** → {event.action}")

            time.sleep(0.15)

    except Exception as e:
        st.error(f"❌ Agent error: {str(e)}")
        st.exception(e)
        st.session_state.running = False
        return

    # Mark all done
    st.session_state.active_agents = set()
    st.session_state.done_agents = {"Orchestrator", "Retrieval", "Execution", "Verification", "Audit"}
    with pipeline_placeholder.container():
        render_agent_pipeline(set(), st.session_state.done_agents, st.session_state.error_agents)

    status_placeholder.success("✅ Workflow completed autonomously — all steps executed, audit trail saved.")
    st.session_state.running = False
    st.session_state.completed = True

    # ── Final Summary ──
    st.markdown("---")
    st.markdown("### 🏁 Execution Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Steps", len(st.session_state.steps))
    with c2:
        errors = sum(1 for s in st.session_state.steps if s.get("error"))
        st.metric("Errors Recovered", errors)
    with c3:
        st.metric("Human Interventions", 0)
    with c4:
        st.metric("Audit Records", len(st.session_state.audit_trail))

    # Audit trail download
    if st.session_state.audit_trail:
        df = pd.DataFrame(st.session_state.audit_trail)
        st.download_button(
            "📥 Download Audit Trail (CSV)",
            data=df.to_csv(index=False),
            file_name=f"workflowmind_audit_{scenario_fn_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )


# ─── Scenario 1: Employee Onboarding ─────────────────────────────────────────
with tab1:
    st.markdown("""
    <div class="scenario-card">
        <div class="scenario-title">🧑‍💼 Scenario: New Employee Onboarding with Error Recovery</div>
        <div class="scenario-desc">
            A new backend engineer joins on Monday. The agent must autonomously:
            provision accounts across 5 enterprise systems, assign an onboarding buddy,
            schedule orientation meetings, and send a personalised welcome email —
            all without human intervention. Midway through, JIRA returns a 503 error.
            The agent detects this, retries, and if needed, escalates to IT support.
        </div>
        <span class="tag tag-blue">5 Systems Provisioned</span>
        <span class="tag tag-green">Auto Error Recovery</span>
        <span class="tag tag-orange">IT Escalation Logic</span>
        <span class="tag tag-blue">Buddy Assignment</span>
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        btn1 = st.button("▶ Run Onboarding Agent", key="btn_onboarding",
                         type="primary", use_container_width=True,
                         disabled=st.session_state.running)
    with col_info:
        st.markdown("""
        **New Employee:** Ananya Gupta · Backend Engineer · Engineering Dept
        **Expected:** 7+ autonomous steps · JIRA failure injected at step 3 · Full audit trail
        """)

    if btn1:
        st.markdown("### 🔀 Agent Pipeline")
        run_scenario("onboarding")


# ─── Scenario 2: Meeting Intelligence ────────────────────────────────────────
with tab2:
    st.markdown("""
    <div class="scenario-card">
        <div class="scenario-title">🗣️ Scenario: Meeting Transcript → Action Items → JIRA</div>
        <div class="scenario-desc">
            A sprint planning meeting with 4 participants has just ended.
            The agent retrieves the transcript, extracts all action items, intelligently assigns
            owners based on context, creates JIRA tickets, flags ONE ambiguous item
            (analytics dashboard ownership — unclear who owns it), and sends a complete
            summary to all participants — zero manual follow-up.
        </div>
        <span class="tag tag-blue">NLP Action Extraction</span>
        <span class="tag tag-orange">Ambiguity Detection</span>
        <span class="tag tag-green">Auto JIRA Tickets</span>
        <span class="tag tag-blue">Participant Summary</span>
    </div>
    """, unsafe_allow_html=True)

    col_btn2, col_info2 = st.columns([1, 3])
    with col_btn2:
        btn2 = st.button("▶ Run Meeting Agent", key="btn_meeting",
                         type="primary", use_container_width=True,
                         disabled=st.session_state.running)
    with col_info2:
        st.markdown("""
        **Meeting:** Q2 Sprint Planning — Team Nexus · 4 participants
        **Expected:** Action item extraction · 1 ambiguous item flagged · JIRA tickets created
        """)

    if btn2:
        st.markdown("### 🔀 Agent Pipeline")
        run_scenario("meeting")


# ─── Scenario 3: SLA Breach Prevention ───────────────────────────────────────
with tab3:
    st.markdown("""
    <div class="scenario-card">
        <div class="scenario-title">🚨 Scenario: SLA Breach Prevention — Procurement Bottleneck</div>
        <div class="scenario-desc">
            A ₹4.5 lakh vendor contract renewal approval has been stuck for 49 hours
            (SLA was 24 hours). The primary approver (VP Product) is on leave.
            The agent detects the bottleneck, identifies the delegate approver in the
            approval hierarchy (CTO), reassigns the request, logs a SOX-compliant
            override, and notifies all stakeholders — preventing a financial penalty.
        </div>
        <span class="tag tag-red">SLA Already Breached</span>
        <span class="tag tag-orange">Hierarchy Navigation</span>
        <span class="tag tag-green">Auto Delegation</span>
        <span class="tag tag-blue">SOX Audit Log</span>
    </div>
    """, unsafe_allow_html=True)

    col_btn3, col_info3 = st.columns([1, 3])
    with col_btn3:
        btn3 = st.button("▶ Run SLA Guard Agent", key="btn_sla",
                         type="primary", use_container_width=True,
                         disabled=st.session_state.running)
    with col_info3:
        st.markdown("""
        **Request:** PR-2847 · Vendor Contract Renewal · ₹4,50,000
        **Expected:** Bottleneck detection · Delegate found · Approval reassigned · Audit logged
        """)

    if btn3:
        st.markdown("### 🔀 Agent Pipeline")
        run_scenario("sla_breach")


# ─── Tab 4: Full Audit Trail ──────────────────────────────────────────────────
with tab4:
    st.markdown("### 📋 Full Audit Trail")
    st.markdown("""
    Every decision made by every agent is logged here in real time.
    This is your **enterprise compliance record** — timestamped, agent-attributed, and exportable.
    """)

    if st.session_state.audit_trail:
        df = pd.DataFrame(st.session_state.audit_trail)
        df.index += 1

        # Colour status column
        def style_status(val):
            if "error" in str(val).lower():
                return "color: #e05252; font-weight: bold;"
            if "success" in str(val).lower() or "complete" in str(val).lower():
                return "color: #5cb85c; font-weight: bold;"
            return "color: #e0e0e0;"

        styled = df.style.applymap(style_status, subset=["status"])
        st.dataframe(styled, use_container_width=True, height=500)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "📥 Download as CSV",
                data=df.to_csv(index=False),
                file_name=f"workflowmind_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        with col_dl2:
            st.download_button(
                "📥 Download as JSON",
                data=df.to_json(orient="records", indent=2),
                file_name=f"workflowmind_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

        # Stats
        st.markdown("#### Summary")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Agent Actions", len(df))
        with c2:
            agent_counts = df["agent"].value_counts()
            st.metric("Most Active Agent", agent_counts.index[0] if not agent_counts.empty else "N/A")
        with c3:
            error_count = df[df["status"] == "error"].shape[0]
            st.metric("Errors Recovered", error_count)
    else:
        st.info("Run a scenario to populate the audit trail.")

        # Show sample audit structure
        st.markdown("#### Expected Audit Trail Structure")
        sample = pd.DataFrame([
            {"timestamp": "10:23:01", "agent": "Orchestrator", "action": "Initialising workflow", "status": "planning", "details": "..."},
            {"timestamp": "10:23:04", "agent": "Retrieval",    "action": "Called `get_employee_info`", "status": "success", "details": "..."},
            {"timestamp": "10:23:07", "agent": "Execution",    "action": "Called `create_account`", "status": "error", "details": "JIRA 503"},
            {"timestamp": "10:23:10", "agent": "Execution",    "action": "Called `create_account` (retry)", "status": "success", "details": "..."},
        ])
        st.dataframe(sample, use_container_width=True)


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#556080; font-size:0.85rem; padding:16px 0;">
    <b style="color:#4A90D9;">WorkflowMind AI</b> · Powered by Multi-Agent Function Calling<br><br>
    Made with ❤️ for Economic Times by Team Synora
</div>
""", unsafe_allow_html=True)
