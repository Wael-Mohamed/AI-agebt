from agents.base import BaseAgent


class QualifierAgent(BaseAgent):
    """
    Qualifies leads using the BANT framework (Budget, Authority, Need, Timeline).
    Outputs a qualification score and recommended next pipeline stage.
    """

    name = "QualifierAgent"

    system_prompt = """You are an expert B2B sales qualification specialist using the BANT framework.

Your job:
1. Analyze the lead information provided.
2. Assess Budget, Authority, Need, and Timeline signals.
3. Assign a qualification SCORE (0-100):
   - 0-25:  Unqualified — missing most BANT criteria
   - 26-50: Weak — some criteria present but major gaps
   - 51-75: Qualified — most criteria met, worth pursuing
   - 76-100: Hot lead — all criteria met, prioritize immediately
4. Identify key pain points from the conversation.
5. Update the lead in the CRM with score, BANT details, and move to QUALIFYING stage.
6. Recommend next action: nurture, schedule demo, send proposal, or disqualify.

Always call update_lead to save qualification data and log_activity to record your assessment.
Be concise and actionable in your recommendations."""

    def qualify(self, lead_id: str, conversation: str) -> str:
        prompt = (
            f"Qualify this lead.\n\n"
            f"Lead ID: {lead_id}\n\n"
            f"Conversation / info provided:\n{conversation}\n\n"
            f"First get lead details, then assess BANT criteria, update the lead with your findings, "
            f"log a 'note' activity, and provide your qualification verdict."
        )
        return self.run(prompt)
