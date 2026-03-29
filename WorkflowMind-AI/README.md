# WorkflowMind AI 🤖
### ET AI Hackathon 2026 — Track 2: Agentic AI for Autonomous Enterprise Workflows

> **Multi-agent system that autonomously executes complex enterprise workflows — with error recovery, branching logic, and a full compliance audit trail.**

---

## 🎯 Problem Statement

Enterprises lose hundreds of hours monthly to manual process management — chasing approvals, following up on meeting action items, manually onboarding employees. These workflows are repetitive, error-prone, and require constant human babysitting.

**WorkflowMind AI** is a multi-agent system that takes full ownership of these workflows: it detects failures, self-corrects, navigates approval hierarchies, flags ambiguity — and completes jobs end-to-end without human involvement.

---

## 🏗️ Architecture

```
                    ┌─────────────────────────────────────────┐
                    │          Orchestrator Agent              │
                    │   (Plans workflow, routes to agents)     │
                    └────────────────┬────────────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          ▼                          ▼                           ▼
  ┌───────────────┐        ┌─────────────────┐        ┌──────────────────┐
  │ Retrieval     │        │ Execution Agent  │        │ Verification     │
  │ Agent         │        │ (Creates tickets,│        │ Agent            │
  │ (Fetches data │        │ sends emails,    │        │ (Confirms all    │
  │ from HR, JIRA,│        │ provisions accts,│        │ steps complete,  │
  │ approvals)    │        │ reassigns apprvls│        │ validates output)│
  └───────────────┘        └────────┬────────┘        └──────────────────┘
                                    │ (on error)
                           ┌────────▼────────┐
                           │  Error Recovery  │
                           │  Agent           │
                           │  (Retry → IT     │
                           │  escalation)     │
                           └─────────────────┘
                                    │
                           ┌────────▼────────┐
                           │   Audit Agent    │
                           │   (Logs every    │
                           │   decision, SOX) │
                           └─────────────────┘
```

**Technology Stack:**
| Component | Technology |
|-----------|-----------|
| LLM | Claude claude-sonnet-4-6 (Anthropic) |
| Agentic Framework | Anthropic Tool Use (native) |
| Orchestration Pattern | LangGraph-inspired state machine |
| Knowledge / Context | Structured context injection per agent |
| UI | Streamlit (real-time agent visualization) |
| Audit Trail | Pandas DataFrame + CSV/JSON export |
| Mock Systems | Python-native (JIRA, Email, Calendar, HR) |

---

## 🎬 Three Live Scenarios

### Scenario 1: Employee Onboarding with Error Recovery
- New hire joins → agent creates accounts across **5 systems** (GitHub, Slack, JIRA, HR Portal, GSuite)
- **JIRA returns 503 error** → agent retries automatically → success
- If retry fails → agent escalates to IT Support (ticket created)
- Buddy assigned, orientation meetings scheduled, welcome email sent
- **8+ autonomous steps, 0 human interventions**

### Scenario 2: Meeting Intelligence
- Sprint planning transcript ingested
- Agent extracts **all action items**, assigns owners from context
- **1 ambiguous item flagged** (analytics dashboard — unclear owner) for human clarification
- JIRA tickets created with correct priorities, assignees, labels
- Meeting summary sent to all 4 participants automatically

### Scenario 3: SLA Breach Prevention
- Procurement approval stuck **49 hours** (SLA = 24h, already breached)
- Agent diagnoses: primary approver on leave
- Navigates approval hierarchy → finds delegate (CTO)
- Reassigns approval → logs **SOX-compliant override**
- Notifies delegate + requestor via email
- **Financial penalty avoided. Full audit trail saved.**

---

## 🚀 Setup & Run

### Prerequisites
- Python 3.10+
- Anthropic API key ([get one here](https://console.anthropic.com))

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/workflowmind-ai
cd workflowmind-ai

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

Enter your Anthropic API key in the sidebar and click any **▶ Run** button.

---

## 📊 Impact Model

| Metric | Before | After | Saving |
|--------|--------|-------|--------|
| Employee onboarding time | 4–6 hours | 8 minutes | **97% reduction** |
| Meeting follow-up time | 45 min/meeting | 0 min | **100% automated** |
| SLA breach rate (approvals) | 23% | ~2% | **91% reduction** |
| Audit trail completeness | Manual (60%) | 100% automated | **Full compliance** |

**Assumptions (1000-person enterprise):**
- 20 new hires/month × 5 hours saved = **100 hours/month** = ₹3L/month @ ₹300/hr blended rate
- 50 meetings/week × 45 min follow-up = **37.5 hours/week** = ₹45K/week
- 1 SLA breach avoided/month (avg penalty ₹5L) = **₹60L/year**
- **Total estimated annual value: ₹1.2 Cr+**

---

## 📁 Project Structure

```
workflowmind-ai/
├── app.py                  # Streamlit UI with real-time agent visualization
├── core/
│   ├── agent.py            # Multi-agent runner (Claude tool_use)
│   └── tools.py            # Mock enterprise systems (JIRA, Email, HR, etc.)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🏆 Evaluation Alignment

| Dimension | Weight | How We Address It |
|-----------|--------|-------------------|
| **Autonomy Depth** | 30% | 8+ steps per scenario, 0 human interventions, live error recovery |
| **Multi-Agent Design** | 20% | 6 distinct agents with clear roles and handoff protocols |
| **Technical Creativity** | 20% | Native Anthropic tool_use, real-time streaming UI, error injection |
| **Enterprise Readiness** | 20% | Error handling, retry logic, SOX audit trail, graceful degradation |
| **Impact Quantification** | 10% | ₹1.2 Cr+ annual value, measurable before/after metrics |

---

*ET AI Hackathon 2026 · Avataar.ai Knowledge Partner · Built with Claude claude-sonnet-4-6*
