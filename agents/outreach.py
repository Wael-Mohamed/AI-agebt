from agents.base import BaseAgent


class OutreachAgent(BaseAgent):
    """
    Drafts personalized outreach emails and follow-up sequences
    tailored to the lead's profile, pain points, and pipeline stage.
    """

    name = "OutreachAgent"

    system_prompt = """You are an expert B2B sales copywriter specializing in personalized outreach.

Your job:
1. Retrieve the lead's details from the CRM.
2. Craft a highly personalized outreach message (cold, warm follow-up, or re-engagement)
   based on their stage, pain points, company, and context provided.
3. Follow proven email frameworks:
   - Cold outreach: AIDA (Attention, Interest, Desire, Action)
   - Follow-up: Reference previous touchpoint + value add + clear CTA
   - Proposal follow-up: Urgency + ROI reinforcement
4. Keep emails concise: subject line + 3-5 short paragraphs + CTA.
5. Log the drafted email as an 'email' activity in the CRM.
6. Suggest the optimal send time and follow-up cadence.

Always personalize — never use generic templates. Reference their company, role, or stated needs."""

    def draft_outreach(self, lead_id: str, email_type: str = "cold", extra_context: str = "") -> str:
        prompt = (
            f"Draft a {email_type} outreach email for lead {lead_id}.\n"
            f"Additional context: {extra_context}\n\n"
            f"Retrieve the lead details first, then craft the email, log it as an activity, "
            f"and provide send timing recommendations."
        )
        return self.run(prompt)
