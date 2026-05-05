import json
from typing import Any

import anthropic

from config import MODEL, MAX_TOKENS
from tools.crm_tools import CRMStore, get_crm_tool_definitions, handle_crm_tool_call
from agents.qualifier import QualifierAgent
from agents.outreach import OutreachAgent
from agents.objection_handler import ObjectionHandlerAgent
from agents.closer import CloserAgent
from agents.analyzer import AnalyzerAgent


_ROUTING_SYSTEM = """You are the Sales Orchestrator — the central router for a multi-agent AI sales system.

Your agents and when to use them:
- qualifier:    New leads needing evaluation, or re-qualification of existing leads
- outreach:     Drafting cold emails, follow-ups, or nurture sequences
- objection:    When a lead raises a concern, price pushback, or hesitation
- closer:       Ready-to-close deals (score ≥ 60, stage PROPOSAL or NEGOTIATION)
- analyzer:     Pipeline health reports, performance analysis, strategic recommendations
- crm:          Simple CRM operations (create lead, check stage, update fields)

Given the user's request, respond with ONLY a JSON object:
{
  "agent": "<qualifier|outreach|objection|closer|analyzer|crm>",
  "lead_id": "<id or null>",
  "action": "<brief action description>",
  "reasoning": "<one sentence why>"
}"""


class OrchestratorAgent:
    """
    Central router that analyzes requests and delegates to the correct specialist agent.
    Implements the multi-agent feedback loop with retry logic for failures.
    """

    name = "OrchestratorAgent"

    def __init__(self, client: anthropic.Anthropic, crm: CRMStore):
        self.client = client
        self.crm = crm
        self.agents = {
            "qualifier": QualifierAgent(client, crm),
            "outreach": OutreachAgent(client, crm),
            "objection": ObjectionHandlerAgent(client, crm),
            "closer": CloserAgent(client, crm),
            "analyzer": AnalyzerAgent(client, crm),
        }
        self.tools = get_crm_tool_definitions()

    def route(self, user_input: str) -> tuple[str, str]:
        """
        Route the request to the correct agent.
        Returns (agent_name, response).
        """
        routing = self._decide_route(user_input)
        agent_name = routing.get("agent", "crm")
        lead_id = routing.get("lead_id")
        action = routing.get("action", user_input)

        # Direct CRM operations handled by orchestrator itself
        if agent_name == "crm":
            result = self._handle_crm_direct(user_input)
            return "orchestrator", result

        agent = self.agents.get(agent_name)
        if not agent:
            return "orchestrator", f"Unknown agent: {agent_name}"

        # Build enriched prompt for the specialist agent
        enriched = self._enrich_prompt(agent_name, action, lead_id, user_input)

        for attempt in range(3):
            try:
                response = agent.run(enriched)
                if response and len(response) > 20:
                    return agent_name, response
            except Exception as e:
                if attempt == 2:
                    return agent_name, f"Agent encountered an error after 3 attempts: {e}"
                continue

        return agent_name, "Agent did not produce a valid response."

    # ── Private helpers ───────────────────────────────────────────────────

    def _decide_route(self, user_input: str) -> dict:
        """Call Claude to decide which agent should handle the request."""
        try:
            resp = self.client.messages.create(
                model=MODEL,
                max_tokens=256,
                system=_ROUTING_SYSTEM,
                messages=[{"role": "user", "content": user_input}],
            )
            text = resp.content[0].text.strip()
            # Extract JSON even if wrapped in markdown
            if "```" in text:
                text = text.split("```")[1].lstrip("json").strip()
            return json.loads(text)
        except Exception:
            return {"agent": "analyzer", "lead_id": None, "action": user_input}

    def _enrich_prompt(self, agent_name: str, action: str, lead_id: str | None, original: str) -> str:
        parts = [original]
        if lead_id:
            parts.append(f"\n[Lead ID for this task: {lead_id}]")
        return "\n".join(parts)

    def _handle_crm_direct(self, user_input: str) -> str:
        """Handle simple CRM queries directly without spawning a specialist agent."""
        from agents.base import BaseAgent
        agent = BaseAgent(self.client, self.crm)
        agent.system_prompt = (
            "You are a CRM assistant. Use the available tools to fulfill the user's request. "
            "Be concise and show results in a readable format."
        )
        return agent.run(user_input)
