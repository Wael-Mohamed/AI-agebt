"""
Incident Commander Agent
========================
Triages Sentry alerts, opens Linear tickets, and drives the Slack war room.

Integrations (via MCP or stub clients):
  Sentry  → event payload, stack trace, affected users, volume trend
  GitHub  → commits in the last 72h touching the top-frame file
  Linear  → create / update incident ticket
  Slack   → post + update threaded war-room messages

Run standalone:  python -m agents.incident_commander <SENTRY_ISSUE_ID>
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import anthropic

from config import MAX_TOKENS


MODEL = "claude-opus-4-6"

# ── Severity thresholds ──────────────────────────────────────────────────────
SEV_THRESHOLDS = {
    "SEV1": {"affected_users": 1000, "label": "🔴 SEV1 — Critical"},
    "SEV2": {"affected_users": 100,  "label": "🟠 SEV2 — Major"},
    "SEV3": {"affected_users": 10,   "label": "🟡 SEV3 — Minor"},
    "SEV4": {"affected_users": 0,    "label": "🟢 SEV4 — Low"},
}

SYSTEM_PROMPT = """You are an on-call incident commander. When handed a Sentry issue ID or error fingerprint:

1. Pull the full event payload, stack trace, release tag, and affected-user count from Sentry.
2. Grep the repo for the top frame's file path and surrounding commits (last 72h).
3. Open a Linear incident ticket with severity, suspected blast radius, and rollback recommendation.
4. Post a threaded status to the incident Slack channel: what broke, who's looking, ETA for next update.
5. Every 15 minutes, re-check Sentry event volume and update the thread until the incident is closed.

Be decisive. If you're >70% confident it's a specific deploy, say so and recommend the revert.

Available tools:
- sentry_get_issue: Fetch full event payload, stack trace, release, affected users
- sentry_get_volume: Get event volume trend (last 1h in 5-min buckets)
- github_recent_commits: Get commits from the last 72h touching a file path
- linear_create_ticket: Open a Linear incident ticket
- linear_update_ticket: Update an existing Linear ticket
- slack_post_message: Post to the incident channel
- slack_update_message: Update an existing Slack message (for status threads)

Severity classification:
  SEV1: >1000 affected users or full outage
  SEV2: >100 affected users or major feature broken
  SEV3: >10 affected users or degraded performance
  SEV4: <10 affected users or cosmetic issue"""


# ── Stub tool definitions (replace with real MCP calls in production) ────────

def get_tool_definitions() -> list[dict]:
    return [
        {
            "name": "sentry_get_issue",
            "description": "Fetch full event payload, stack trace, release tag, and affected-user count for a Sentry issue.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "Sentry issue ID or fingerprint"},
                },
                "required": ["issue_id"],
            },
        },
        {
            "name": "sentry_get_volume",
            "description": "Get event volume trend for a Sentry issue (last 1h, 5-min buckets).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string"},
                },
                "required": ["issue_id"],
            },
        },
        {
            "name": "github_recent_commits",
            "description": "Get commits from the last 72h that touch a specific file path.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Repo-relative file path from stack trace"},
                    "repo": {"type": "string", "description": "owner/repo"},
                },
                "required": ["file_path", "repo"],
            },
        },
        {
            "name": "linear_create_ticket",
            "description": "Open a Linear incident ticket with severity, blast radius, and rollback recommendation.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "severity": {"type": "string", "enum": ["SEV1", "SEV2", "SEV3", "SEV4"]},
                    "description": {"type": "string", "description": "Full incident description in Markdown"},
                    "suspected_cause": {"type": "string"},
                    "rollback_recommendation": {"type": "string"},
                },
                "required": ["title", "severity", "description"],
            },
        },
        {
            "name": "linear_update_ticket",
            "description": "Update an existing Linear incident ticket (status, new findings).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["In Progress", "Mitigated", "Resolved"]},
                    "comment": {"type": "string"},
                },
                "required": ["ticket_id"],
            },
        },
        {
            "name": "slack_post_message",
            "description": "Post a message to the incident Slack channel. Returns message timestamp for threading.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Slack channel name e.g. #incidents"},
                    "text": {"type": "string"},
                    "thread_ts": {"type": "string", "description": "Thread timestamp to reply in thread"},
                },
                "required": ["channel", "text"],
            },
        },
        {
            "name": "slack_update_message",
            "description": "Update an existing Slack message (e.g. status update in the war room thread).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "ts": {"type": "string", "description": "Message timestamp to update"},
                    "text": {"type": "string"},
                },
                "required": ["channel", "ts", "text"],
            },
        },
    ]


# ── Stub tool execution (wire to real MCP clients in production) ─────────────

@dataclass
class IncidentState:
    issue_id: str
    linear_ticket_id: str = ""
    slack_thread_ts: str = ""
    severity: str = "SEV3"
    affected_users: int = 0
    suspected_commit: str = ""
    open: bool = True
    checks: int = 0
    events: list[dict] = field(default_factory=list)


def execute_tool(tool_name: str, tool_input: dict, state: IncidentState) -> str:
    """
    Stub implementations — replace these with real MCP client calls:
      sentry  → httpx call to mcp.sentry.dev/mcp
      linear  → httpx call to mcp.linear.app/mcp
      slack   → httpx call to mcp.slack.com/mcp
      github  → httpx call to api.githubcopilot.com/mcp
    """
    now = datetime.utcnow().isoformat()

    if tool_name == "sentry_get_issue":
        # Simulate a realistic Sentry payload
        return json.dumps({
            "id": state.issue_id,
            "title": "TypeError: Cannot read properties of undefined (reading 'userId')",
            "culprit": "src/api/checkout.ts in processPayment",
            "release": "v2.14.3",
            "first_seen": "2026-05-03T08:42:00Z",
            "last_seen": now,
            "count": 847,
            "user_count": 312,
            "platform": "node",
            "stack_trace": [
                {"file": "src/api/checkout.ts", "line": 94, "function": "processPayment"},
                {"file": "src/lib/stripe.ts",   "line": 41, "function": "chargeCard"},
                {"file": "src/middleware/auth.ts","line": 17, "function": "requireUser"},
            ],
            "tags": {"environment": "production", "server": "checkout-worker-3"},
        })

    if tool_name == "sentry_get_volume":
        return json.dumps({
            "issue_id": state.issue_id,
            "buckets_5min": [2, 4, 18, 67, 143, 201, 198, 186, 27],
            "trend": "spiked at 08:45 UTC, now declining",
            "peak_rate": "201 events/5min",
        })

    if tool_name == "github_recent_commits":
        return json.dumps({
            "file": tool_input.get("file_path"),
            "commits": [
                {
                    "sha": "a3f9c12",
                    "author": "dev@example.com",
                    "message": "refactor: simplify auth middleware token parsing",
                    "timestamp": "2026-05-03T07:11:00Z",
                    "files_changed": ["src/middleware/auth.ts", "src/api/checkout.ts"],
                },
                {
                    "sha": "b84e201",
                    "author": "dev2@example.com",
                    "message": "fix: handle null session in checkout",
                    "timestamp": "2026-05-02T19:22:00Z",
                    "files_changed": ["src/api/checkout.ts"],
                },
            ],
        })

    if tool_name == "linear_create_ticket":
        ticket_id = f"INC-{int(time.time()) % 10000}"
        state.linear_ticket_id = ticket_id
        state.severity = tool_input.get("severity", "SEV3")
        return json.dumps({
            "status": "created",
            "ticket_id": ticket_id,
            "url": f"https://linear.app/team/INC/{ticket_id}",
            "severity": tool_input.get("severity"),
        })

    if tool_name == "linear_update_ticket":
        return json.dumps({
            "status": "updated",
            "ticket_id": tool_input.get("ticket_id"),
            "new_status": tool_input.get("status"),
        })

    if tool_name == "slack_post_message":
        ts = f"{time.time():.6f}"
        if not state.slack_thread_ts:
            state.slack_thread_ts = ts
        channel = tool_input.get("channel", "#incidents")
        text_preview = tool_input.get("text", "")[:80]
        print(f"\n[Slack → {channel}] {text_preview}...")
        return json.dumps({"ok": True, "ts": ts, "channel": channel})

    if tool_name == "slack_update_message":
        print(f"\n[Slack update → {tool_input.get('channel')}] {tool_input.get('text', '')[:80]}...")
        return json.dumps({"ok": True, "ts": tool_input.get("ts")})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ── Core agent loop ──────────────────────────────────────────────────────────

class IncidentCommanderAgent:
    """
    Agentic loop that:
      1. Triages the Sentry alert (initial investigation)
      2. Opens Linear ticket + Slack war room
      3. Polls every 15 min and posts status updates until closed
    """

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.tools = get_tool_definitions()

    def triage(self, issue_id: str) -> IncidentState:
        """Run full triage for a Sentry issue. Returns final incident state."""
        state = IncidentState(issue_id=issue_id)
        print(f"\n[IncidentCommander] Starting triage for Sentry issue: {issue_id}")

        prompt = (
            f"Sentry issue ID: {issue_id}\n\n"
            f"Begin full incident triage:\n"
            f"1. Fetch the Sentry issue details and volume trend.\n"
            f"2. Identify the top stack-frame file and check GitHub commits (last 72h) for repo 'myorg/myapp'.\n"
            f"3. Classify severity and open a Linear incident ticket.\n"
            f"4. Post the initial war-room message to #incidents.\n"
            f"5. Provide your incident summary and rollback recommendation."
        )

        self._run_loop(prompt, state)
        return state

    def check_in(self, state: IncidentState) -> str:
        """15-minute check-in: re-fetch volume, update Slack thread and Linear ticket."""
        state.checks += 1
        prompt = (
            f"15-minute check-in #{state.checks} for Sentry issue {state.issue_id}.\n"
            f"Linear ticket: {state.linear_ticket_id}\n"
            f"Slack thread ts: {state.slack_thread_ts}\n\n"
            f"1. Re-fetch Sentry event volume.\n"
            f"2. Post a status update in the existing Slack thread.\n"
            f"3. Update the Linear ticket with latest findings.\n"
            f"4. Declare status: escalating / stable / mitigating / resolved."
        )
        return self._run_loop(prompt, state)

    def _run_loop(self, prompt: str, state: IncidentState) -> str:
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        system = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]

        for _ in range(15):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=messages,
                tools=self.tools,
            )

            text_parts, tool_calls = [], []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            if response.stop_reason == "end_turn" or not tool_calls:
                final = "\n".join(text_parts).strip()
                if final:
                    print(f"\n[IncidentCommander]\n{final}")
                return final

            messages.append({"role": "assistant", "content": response.content})

            results = []
            for tc in tool_calls:
                print(f"  → calling {tc.name}({json.dumps(tc.input)[:60]}...)")
                result = execute_tool(tc.name, tc.input, state)
                results.append({"type": "tool_result", "tool_use_id": tc.id, "content": result})

            messages.append({"role": "user", "content": results})

        return "Max iterations reached."


# ── Polling loop ─────────────────────────────────────────────────────────────

def run_war_room(issue_id: str, poll_interval_seconds: int = 900) -> None:
    """
    Full incident war-room loop:
      triage → wait 15 min → check-in → repeat until closed.

    Set poll_interval_seconds=60 for demo/testing.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    agent = IncidentCommanderAgent(client)

    state = agent.triage(issue_id)

    print(f"\n[IncidentCommander] War room open. Checking in every {poll_interval_seconds}s.")
    print("  Press Ctrl+C to close the incident.\n")

    try:
        while state.open:
            time.sleep(poll_interval_seconds)
            summary = agent.check_in(state)
            if any(word in summary.lower() for word in ("resolved", "closed", "mitigated")):
                print("\n[IncidentCommander] Incident resolved. Closing war room.")
                state.open = False
    except KeyboardInterrupt:
        print("\n[IncidentCommander] Incident closed by commander.")


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    issue = sys.argv[1] if len(sys.argv) > 1 else "ISSUE-12345"
    # Use 60s poll for demo; set to 900 for production
    run_war_room(issue, poll_interval_seconds=60)
