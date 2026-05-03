import json
import uuid
from datetime import datetime
from models.lead import Lead, PipelineStage, Activity


class CRMStore:
    """In-memory CRM store shared across all agents."""

    def __init__(self):
        self._leads: dict[str, Lead] = {}

    # ── Public helpers ────────────────────────────────────────────────────

    def create_lead(self, name: str, company: str, email: str) -> Lead:
        lead_id = str(uuid.uuid4())[:8]
        lead = Lead(id=lead_id, name=name, company=company, email=email)
        self._leads[lead_id] = lead
        return lead

    def get_lead(self, lead_id: str) -> Lead | None:
        return self._leads.get(lead_id)

    def get_all_leads(self) -> list[Lead]:
        return list(self._leads.values())

    # ── Tool call handlers ────────────────────────────────────────────────

    def save_lead(self, name: str, company: str, email: str) -> dict:
        lead = self.create_lead(name, company, email)
        return {"status": "created", "lead_id": lead.id, "lead": lead.to_dict()}

    def update_lead(self, lead_id: str, **kwargs) -> dict:
        lead = self.get_lead(lead_id)
        if not lead:
            return {"status": "error", "message": f"Lead {lead_id} not found"}
        for key, value in kwargs.items():
            if key == "stage":
                try:
                    lead.stage = PipelineStage(value)
                except ValueError:
                    return {"status": "error", "message": f"Invalid stage: {value}"}
            elif key == "pain_points" and isinstance(value, list):
                lead.pain_points.extend(value)
            elif key == "objections" and isinstance(value, list):
                lead.objections.extend(value)
            elif hasattr(lead, key):
                setattr(lead, key, value)
        lead.updated_at = datetime.now().isoformat()
        return {"status": "updated", "lead": lead.to_dict()}

    def log_activity(self, lead_id: str, activity_type: str, content: str, agent: str) -> dict:
        lead = self.get_lead(lead_id)
        if not lead:
            return {"status": "error", "message": f"Lead {lead_id} not found"}
        activity = Activity(type=activity_type, content=content, agent=agent)
        lead.activities.append(activity)
        lead.updated_at = datetime.now().isoformat()
        return {"status": "logged", "activity": {"type": activity_type, "agent": agent}}

    def get_pipeline_summary(self) -> dict:
        summary: dict[str, list] = {stage.value: [] for stage in PipelineStage}
        for lead in self._leads.values():
            summary[lead.stage.value].append(
                {"id": lead.id, "name": lead.name, "company": lead.company, "score": lead.score}
            )
        return {"pipeline": summary, "total_leads": len(self._leads)}

    def get_lead_details(self, lead_id: str) -> dict:
        lead = self.get_lead(lead_id)
        if not lead:
            return {"status": "error", "message": f"Lead {lead_id} not found"}
        data = lead.to_dict()
        data["activities"] = [
            {"type": a.type, "agent": a.agent, "content": a.content[:200], "timestamp": a.timestamp}
            for a in lead.activities[-5:]
        ]
        return {"status": "ok", "lead": data}


def get_crm_tool_definitions() -> list[dict]:
    """Returns Anthropic-format tool definitions for all CRM operations."""
    return [
        {
            "name": "save_lead",
            "description": "Create a new lead in the CRM.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the lead"},
                    "company": {"type": "string", "description": "Company name"},
                    "email": {"type": "string", "description": "Email address"},
                },
                "required": ["name", "company", "email"],
            },
        },
        {
            "name": "update_lead",
            "description": (
                "Update lead fields. Updatable fields: stage (NEW, QUALIFYING, NURTURING, "
                "PROPOSAL, NEGOTIATION, CLOSED_WON, CLOSED_LOST), score (0-100), budget, "
                "authority, need, timeline, pain_points (list), objections (list), notes."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string"},
                    "stage": {"type": "string"},
                    "score": {"type": "integer"},
                    "budget": {"type": "string"},
                    "authority": {"type": "string"},
                    "need": {"type": "string"},
                    "timeline": {"type": "string"},
                    "pain_points": {"type": "array", "items": {"type": "string"}},
                    "objections": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string"},
                },
                "required": ["lead_id"],
            },
        },
        {
            "name": "log_activity",
            "description": "Log a sales activity (email, call, note, stage_change) for a lead.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string"},
                    "activity_type": {
                        "type": "string",
                        "enum": ["email", "call", "note", "stage_change"],
                    },
                    "content": {"type": "string", "description": "Details of the activity"},
                    "agent": {"type": "string", "description": "Which agent performed this"},
                },
                "required": ["lead_id", "activity_type", "content", "agent"],
            },
        },
        {
            "name": "get_pipeline_summary",
            "description": "Get an overview of all leads grouped by pipeline stage.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "get_lead_details",
            "description": "Get full details and recent activity history for a specific lead.",
            "input_schema": {
                "type": "object",
                "properties": {"lead_id": {"type": "string"}},
                "required": ["lead_id"],
            },
        },
    ]


def handle_crm_tool_call(crm: CRMStore, tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call to the CRM store and return JSON string result."""
    if tool_name == "save_lead":
        result = crm.save_lead(**tool_input)
    elif tool_name == "update_lead":
        result = crm.update_lead(**tool_input)
    elif tool_name == "log_activity":
        result = crm.log_activity(**tool_input)
    elif tool_name == "get_pipeline_summary":
        result = crm.get_pipeline_summary()
    elif tool_name == "get_lead_details":
        result = crm.get_lead_details(**tool_input)
    else:
        result = {"status": "error", "message": f"Unknown tool: {tool_name}"}
    return json.dumps(result)
