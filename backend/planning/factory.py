from typing import Any
from models import PlanType
from .daily_strategy import DailyStrategy
from .weekly_strategy import WeeklyStrategy
from .monthly_strategy import MonthlyStrategy
from .finance_strategy import FinanceStrategy
from rag.manager import RAGManager

class PlanningFactory:
    """
    Factory to create the appropriate planning strategy.
    """
    @staticmethod
    def get_strategy(plan_type: PlanType, llm_client: Any, rag_manager: RAGManager):
        if plan_type == PlanType.FINANCE:
            return FinanceStrategy(llm_client, rag_manager)
        elif plan_type == PlanType.WEEKLY:
            return WeeklyStrategy(llm_client, rag_manager)
        elif plan_type == PlanType.MONTHLY:
            return MonthlyStrategy(llm_client, rag_manager)
        else:
            return DailyStrategy(llm_client, rag_manager)
