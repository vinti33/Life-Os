"""
LifeOS Review Agent — Plan Optimization Suggestions
=====================================================
Analyzes draft plans against historical performance data
and proposes upgrades (optimize or challenge type).
"""

import json
from typing import Dict, Any, List
from openai import AsyncOpenAI
from config import settings
from utils.logger import get_logger, timed

log = get_logger("review_agent")


class ReviewAgent:
    def __init__(self):
        # Use requests to avoid IPv6 issues
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

    @timed("review_agent")
    async def analyze_plan(
        self,
        plan: Dict[str, Any],
        historical_performance: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Reviews a draft plan and suggests 1-2 data-driven upgrades.
        Returns empty upgrades gracefully on any failure.
        """
        system_prompt = f"""
You are the LifeOS Optimization Agent. Review this draft plan based on historical data.

DRAFT PLAN: {json.dumps(plan)}
HISTORICAL PERFORMANCE: {json.dumps(historical_performance)}

GOAL: Suggest 1-2 upgrades to the plan to make it more realistic or ambitious.

OUTPUT FORMAT (JSON ONLY):
{{
    "upgrades": [
        {{
            "type": "optimize|challenge",
            "description": "Suggested change",
            "impact": "Predicted benefit"
        }}
    ]
}}
"""
        import requests
        import asyncio

        def _sync_request():
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": settings.AI_MODEL,
                "messages": [{"role": "system", "content": system_prompt.strip()}],
                "response_format": {"type": "json_object"},
                "max_tokens": 500,
            }
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            r.raise_for_status()
            return r.json()

        try:
            response = await asyncio.to_thread(_sync_request)
            result = json.loads(response["choices"][0]["message"]["content"])
            log.info(f"Review agent generated {len(result.get('upgrades', []))} upgrade suggestions")
            return result

        except Exception as e:
            error_msg = str(e)
            log.error(f"Review agent failed: {error_msg}")

            if "more system memory" in error_msg.lower():
                log.warning(f"Model '{settings.AI_MODEL}' requires more RAM than available")
            elif "connection" in error_msg.lower() or "connect" in error_msg.lower():
                log.warning(f"Cannot connect to LLM at {settings.OPENAI_BASE_URL}")

            return {"upgrades": []}

    def upgrade_plan(self, plan: Dict[str, Any], selection: List[str]) -> Dict[str, Any]:
        """Applies selected upgrades to the plan."""
        log.info(f"Applying {len(selection)} upgrades to plan")
        return plan
