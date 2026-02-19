import json
from typing import Dict, Any, List
from .base_strategy import PlanningStrategy
from schemas.plan_schemas import FinancePlanSchema
from utils.logger import get_logger

log = get_logger("planning.finance")

class FinanceStrategy(PlanningStrategy):
    """
    Generates a structured financial plan including budget and savings.
    """
    async def generate(self, profile: Dict[str, Any], context: str, **kwargs) -> Dict[str, Any]:
        stats = kwargs.get("stats", [])
        patterns = kwargs.get("patterns", [])
        rag_context = await self._query_rag(context)

        system_prompt = self._build_prompt(profile, stats, patterns, context, rag_context)
        
        # Call LLM
        response = await self.llm_client.generate(system_prompt, response_model=FinancePlanSchema)
        
        return response.dict()

    def _build_prompt(self, profile, stats, patterns, context, rag_context):
        return f"""Financial Advisor.
RULES:
1. JSON ONLY. No markdown.
2. Extract income, expenses, and savings goals.
3. All numbers must be realistic.
4. "type" MUST be one of: income, expense_fixed, expense_variable, savings, debt_payment.

USER PROFILE: {json.dumps(profile)}
STATS: {json.dumps(stats)}
PATTERNS: {json.dumps(patterns)}
KNOWLEDGE: {rag_context}
REQUEST: "{context}"

OUTPUT FORMAT (JSON ONLY, NO MARKDOWN):
{{
  "plan_summary": "Financial Health Summary",
  "total_income_projected": 0.0,
  "total_expenses_projected": 0.0,
  "savings_goal": 0.0,
  "financial_health_score": 85,
  "items": [
     {{"title": "Rent/Mortgage", "category": "finance", "type": "expense_fixed", "tag": "need|want|investment|waste", "amount": 1000.0, "due_date": "YYYY-MM-DD"}}
  ],
  "ai_insights": [
     {{"item": "Coffee", "verdict": "risky", "reason": "High frequency"}}
  ],
  "clarification_questions": []
}}
"""
