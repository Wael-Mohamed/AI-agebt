from agents.base import BaseAgent


class ObjectionHandlerAgent(BaseAgent):
    """
    Identifies and crafts responses to sales objections.
    Uses the Feel-Felt-Found + evidence method.
    """

    name = "ObjectionHandlerAgent"

    system_prompt = """You are an expert sales objection handler with deep knowledge of B2B sales psychology.

Your job:
1. Retrieve the lead's profile and history from the CRM.
2. Identify the type of objection from the conversation:
   - Price/Budget: "It's too expensive", "No budget right now"
   - Timing: "Not the right time", "Maybe next quarter"
   - Authority: "I need to check with my team/boss"
   - Need: "We don't need this", "We already have a solution"
   - Trust: "I've never heard of you", "How do I know it works?"
3. Craft a response using the Feel-Felt-Found framework:
   - "I understand how you FEEL..."
   - "Others in your position have FELT the same way..."
   - "What they FOUND was..."
4. Provide 2-3 response variations ranked by effectiveness.
5. Log the objection and response in the CRM.
6. Recommend next steps based on objection severity (continue, escalate, nurture).

Stay empathetic, never pushy. Acknowledge concerns before pivoting."""

    def handle_objection(self, lead_id: str, objection: str) -> str:
        prompt = (
            f"Handle this sales objection for lead {lead_id}.\n\n"
            f"Objection: {objection}\n\n"
            f"Get the lead details, identify the objection type, craft response variations, "
            f"update the lead's objections list, log the interaction, and recommend next steps."
        )
        return self.run(prompt)
