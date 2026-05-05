# AI Sales Agent — Multi-Agent System

A production-ready multi-agent AI sales system built with the Anthropic Claude API.

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────────────────┐
│              ORCHESTRATOR AGENT             │
│   Routes requests to the right specialist  │
└────────┬──────┬──────┬──────┬──────┬───────┘
         │      │      │      │      │
    ┌────▼──┐ ┌─▼────┐ ┌─▼──┐ ┌▼────┐ ┌▼──────┐
    │QUALIF.│ │REACH │ │OBJ.│ │CLOSE│ │ANALYZ.│
    │ BANT  │ │Email │ │F-F-│ │Strat│ │Health │
    │ Score │ │Draft │ │Found│ │-egy │ │Report │
    └───┬───┘ └──┬───┘ └─┬──┘ └──┬──┘ └───┬───┘
        │        │        │       │         │
        └────────┴────────┴───────┴─────────┘
                          │
                    ┌─────▼─────┐
                    │  CRM STORE │
                    │(in-memory) │
                    └───────────┘
```

### Agents

| Agent | Role | Framework |
|-------|------|-----------|
| **Orchestrator** | Routes requests, retries on failure | LLM-based routing |
| **Qualifier** | Scores leads 0-100 | BANT (Budget, Authority, Need, Timeline) |
| **Outreach** | Drafts personalized emails | AIDA framework |
| **ObjectionHandler** | Responds to pushback | Feel-Felt-Found |
| **Closer** | Closing strategies | Summary / Assumptive / Urgency close |
| **Analyzer** | Pipeline health & priorities | Data-driven insights |

### Pipeline Stages
`NEW → QUALIFYING → NURTURING → PROPOSAL → NEGOTIATION → CLOSED_WON / CLOSED_LOST`

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Run
python main.py
```

## Usage

```
add lead          → Add a new lead (guided)
pipeline          → Show pipeline overview
analyze           → Run pipeline analysis
qualify <id>      → Qualify a specific lead
email <id>        → Draft outreach email
close <id>        → Execute closing strategy
help              → Show all commands
```

Or type naturally — the Orchestrator routes automatically:
- *"The lead from Acme says they don't have budget"*
- *"Draft a follow-up for lead abc12345"*
- *"Which leads should I focus on today?"*
