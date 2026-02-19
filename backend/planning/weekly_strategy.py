import json
from typing import Dict, Any, List
from .base_strategy import PlanningStrategy
from schemas.plan_schemas import WeeklyPlanSchema
from utils.logger import get_logger

log = get_logger("planning.weekly")

class WeeklyStrategy(PlanningStrategy):
    """
    Generates a structured weekly plan with goals and habits.
    """
    async def generate(self, profile: Dict[str, Any], context: str, **kwargs) -> Dict[str, Any]:
        stats = kwargs.get("stats", [])
        patterns = kwargs.get("patterns", [])
        rag_context = await self._query_rag(context)

        system_prompt = self._build_prompt(profile, stats, patterns, context, rag_context)
        
        # Call LLM
        response = await self.llm_client.generate(system_prompt, response_model=WeeklyPlanSchema)
        
        return response.dict()

    def _build_prompt(self, profile, stats, patterns, context, rag_context):
        return f"""Weekly Planner (Advanced).
RULES:
1. JSON ONLY. No markdown.
2. OUTCOMES: Must be measurable (current vs target).
3. GOALS: Must span standard categories.
4. CAPITAL: Estimate time distribution (Time Capital) across categories.

USER PROFILE: {json.dumps(profile)}
STATS: {json.dumps(stats)}
PATTERNS: {json.dumps(patterns)}
KNOWLEDGE: {rag_context}
REQUEST: "{context}"

OUTPUT FORMAT (JSON ONLY):
{{
  "plan_summary": "Weekly Theme",
  "focus_area": "string",
  "outcomes": [
    {{
      "id": "uuid-1",
      "title": "Launch MVP",
      "metric": "% complete",
      "current_value": 80,
      "target_value": 100,
      "deadline": "Friday"
    }}
  ],
  "goals": [
    {{
      "title": "Finalize API",
      "category": "work",
      "priority": 1,
      "deadline_day": "Wednesday",
      "subtasks": ["subtask 1"],
      "linked_outcome_id": "uuid-1" 
    }}
  ],
  "habits": [
    {{"habit": "Deep Work", "frequency": "daily", "target_days": ["Mon", "Tue"]}}
  ],
  "capital_allocation": [
    {{"category": "work", "resource_type": "time", "amount": 40, "percentage": 60}},
    {{"category": "health", "resource_type": "time", "amount": 10, "percentage": 15}}
  ],
  "clarification_questions": []
}}
"""
