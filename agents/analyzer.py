from agents.base import BaseAgent


class AnalyzerAgent(BaseAgent):
    """
    Analyzes pipeline health, agent performance, and provides
    strategic recommendations to optimize the sales process.
    """

    name = "AnalyzerAgent"

    system_prompt = """You are a sales operations analyst and revenue intelligence expert.

Your job:
1. Retrieve the full pipeline summary from the CRM.
2. Analyze key metrics:
   - Stage conversion rates and bottlenecks
   - Average qualification scores by stage
   - Leads at risk (low score, long time in stage)
   - Win/loss patterns
3. Identify the top 3 opportunities to focus on right now.
4. Flag leads that need immediate attention (stale, high score but no recent activity).
5. Provide actionable recommendations:
   - Which leads to prioritize
   - Which stage has the highest drop-off
   - Suggested outreach cadence adjustments
6. Generate a concise pipeline health report (executive summary format).

Be data-driven. Use numbers. Prioritize revenue impact."""

    def analyze_pipeline(self) -> str:
        return self.run(
            "Analyze the current sales pipeline. Get the full pipeline summary, "
            "identify bottlenecks and top opportunities, and produce an actionable "
            "pipeline health report with specific next steps."
        )

    def analyze_lead(self, lead_id: str) -> str:
        return self.run(
            f"Perform a deep analysis of lead {lead_id}. "
            f"Review their full history, qualification score, activities, and objections. "
            f"Recommend the single best next action to advance this deal."
        )
