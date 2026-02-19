from abc import ABC, abstractmethod
from typing import Dict, Any, List
import asyncio
from rag.manager import RAGManager
from schemas.plan_schemas import PlanBase

class PlanningStrategy(ABC):
    """
    Abstract base strategy for generating different types of plans.
    """
    def __init__(self, llm_client, rag_manager: RAGManager):
        self.llm_client = llm_client
        self.rag_manager = rag_manager

    @abstractmethod
    async def generate(self, profile: Dict[str, Any], context: str, **kwargs) -> Dict[str, Any]:
        """
        Generates a plan based on the profile and context.
        Must return a dictionary matching the specific Pydantic schema for the plan type.
        """
        pass

    async def _query_rag(self, context: str) -> str:
        if self.rag_manager:
            # RAGManager.query is cached and might be async depending on implementation
            # The warning says "coroutine was never awaited", so we must await it.
            # If it's sync, we can wrap it. 
            # Safest is to try await, but since we saw the warning, it IS a coroutine.
            res = self.rag_manager.query(context)
            if asyncio.iscoroutine(res):
                return await res
            return res
        return ""
