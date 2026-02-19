from typing import List, Dict, Any, Optional
from schemas.plan_schemas import DailyPlanSchema, WeeklyPlanSchema, FinancePlanSchema, TransactionType

class ScoreCalculator:
    """
    Implements the scoring algorithms for LifeOS 2.0.
    """

    @staticmethod
    def calculate_daily_score(plan: DailyPlanSchema, completed_tasks: int, total_tasks: int) -> int:
        """
        Calculates Daily Productivity Score (DPS) (0-100).
        DPS = (Completion% * 50) + (Routine_Adherence * 20) + (Focus_Hours_Factor * 30)
        Simplified for now based on available data.
        """
        if total_tasks == 0:
            return 0
        
        completion_ratio = completed_tasks / total_tasks
        
        # Check routines (if they exist in reflection or status)
        # For now, we assume if 80% tasks done, routines likely done or we don't track them yet explicitly in this calc
        
        # Simple weighted score
        score = int(completion_ratio * 100)
        
        return min(100, max(0, score))

    @staticmethod
    def calculate_financial_score(plan: FinancePlanSchema) -> int:
        """
        Calculates Financial Health Score (FHS) (0-100).
        FHS = (Savings Rate * 50) + (Needs/Wants Balance * 30) + (Investment * 20)
        """
        income = plan.total_income_projected
        if income <= 0:
            return 0
            
        expenses = plan.total_expenses_projected
        savings = plan.savings_goal
        
        # 1. Savings Rate (Target 20%)
        # If savings >= 20% of income -> Max points (50)
        savings_rate = savings / income
        savings_score = min(50, (savings_rate / 0.20) * 50)
        
        # 2. Expense Control (Expenses < 80% income)
        expense_ratio = expenses / income
        expense_score = 0
        if expense_ratio <= 0.5: # Excellent
            expense_score = 30
        elif expense_ratio <= 0.8: # Good
            expense_score = 20
        elif expense_ratio <= 1.0: # Warning
            expense_score = 10
        else: # Danger
            expense_score = 0
            
        # 3. Investment Allocation (Bonus 20 points for categorization logic)
        # For now, simpler check: do we have positive savings?
        inv_score = 20 if savings > 0 else 0
        
        final_score = savings_score + expense_score + inv_score
        return int(min(100, max(0, final_score)))

    @staticmethod
    def calculate_lifeos_index(
        daily_scores: List[int],
        weekly_score: int,
        finance_score: int,
        habit_consistency: float
    ) -> int:
        """
        LPI = (Avg_Daily * 0.35) + (Weekly * 0.25) + (Finance * 0.25) + (Habits * 0.15)
        """
        if not daily_scores:
            avg_daily = 0
        else:
            avg_daily = sum(daily_scores) / len(daily_scores)
            
        lpi = (avg_daily * 0.35) + \
              (weekly_score * 0.25) + \
              (finance_score * 0.25) + \
              (habit_consistency * 100 * 0.15)
              
        return int(min(100, max(0, lpi)))
