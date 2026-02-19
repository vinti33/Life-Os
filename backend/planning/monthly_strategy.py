import json
from typing import Dict, Any, List
from .base_strategy import PlanningStrategy
from schemas.plan_schemas import MonthlyPlanSchema
from utils.logger import get_logger

log = get_logger("planning.monthly")

class MonthlyStrategy(PlanningStrategy):
    """
    Generates a structured monthly plan with milestones and KPIs.
    """
    async def generate(self, profile: Dict[str, Any], context: str, **kwargs) -> Dict[str, Any]:
        stats = kwargs.get("stats", [])
        patterns = kwargs.get("patterns", [])
        rag_context = await self._query_rag(context)

        system_prompt = self._build_prompt(profile, stats, patterns, context, rag_context)
        
        # Call LLM
        response = await self.llm_client.generate(system_prompt, response_model=MonthlyPlanSchema)
        
        return response.dict()

    def _build_prompt(self, profile, stats, patterns, context, rag_context):
        return f"""Monthly Planner.
RULES:
1. JSON ONLY. No markdown.
2. Strategic overview. Be specific.
3. High-level milestones with deadlines.
4. "kpi_metric" is optional but recommended.

USER PROFILE: {json.dumps(profile)}
STATS: {json.dumps(stats)}
PATTERNS: {json.dumps(patterns)}
KNOWLEDGE: {rag_context}
REQUEST: "{context}"

OUTPUT FORMAT (JSON ONLY, NO MARKDOWN):
{{
  "plan_summary": "Monthly Objective",
  "theme": "string",
  "strategic_goals": ["Goal 1", "Goal 2"],
  "milestones": [
     {{"title": "Milestone Name", "category": "work|...|", "deadline_date": "YYYY-MM-DD", "status": "pending", "progress": 0}}
  ],
  "kpis": [
     {{"name": "Revenue", "target_value": 5000, "unit": "USD"}}
  ],
  "review_date": "YYYY-MM-DD",
  "clarification_questions": []
}}
"""
