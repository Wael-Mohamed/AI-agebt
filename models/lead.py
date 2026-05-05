from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PipelineStage(str, Enum):
    NEW = "NEW"
    QUALIFYING = "QUALIFYING"
    NURTURING = "NURTURING"
    PROPOSAL = "PROPOSAL"
    NEGOTIATION = "NEGOTIATION"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"


@dataclass
class Activity:
    type: str          # email, call, note, stage_change
    content: str
    agent: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Lead:
    id: str
    name: str
    company: str
    email: str
    stage: PipelineStage = PipelineStage.NEW
    score: int = 0                          # 0-100 qualification score
    budget: Optional[str] = None
    authority: Optional[str] = None        # decision-maker info
    need: Optional[str] = None
    timeline: Optional[str] = None
    pain_points: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    activities: list[Activity] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "company": self.company,
            "email": self.email,
            "stage": self.stage.value,
            "score": self.score,
            "budget": self.budget,
            "authority": self.authority,
            "need": self.need,
            "timeline": self.timeline,
            "pain_points": self.pain_points,
            "objections": self.objections,
            "notes": self.notes,
            "activities_count": len(self.activities),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
