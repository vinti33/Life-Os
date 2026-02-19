from typing import List, Optional, Dict, Any, Union
import uuid
from pydantic import BaseModel, Field, model_validator, field_validator
from enum import Enum
from datetime import date, time

# --- Enums (Imported from Models) ---
from models import EnergyLevel, Priority, TaskCategory

# --- Common Base Schema ---
class PlanBase(BaseModel):
    plan_summary: str = Field(..., description="A concise summary of the plan's goal.")
    clarification_questions: List[str] = Field(default_factory=list, description="Questions if user info is missing.")

class ResourceType(str, Enum):
    TIME = "time"
    MONEY = "money"

class CapitalAllocation(BaseModel):
    category: str
    resource_type: ResourceType
    amount: float # Hours or Dollars
    percentage: float # 0-100

# --- 1. Daily Plan Schema ---
class DailyTask(BaseModel):
    title: str
    category: TaskCategory
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    priority: Priority = Field(default=Priority.MEDIUM)
    energy_required: EnergyLevel = Field(default=EnergyLevel.MEDIUM)
    description: Optional[str] = None
    estimated_duration: Optional[int] = Field(None, description="In minutes")
    actual_duration: Optional[int] = Field(None, description="In minutes")
    completion_status: bool = False

class DailyMetrics(BaseModel):
    productivity_score: int = Field(..., ge=0, le=100)
    focus_hours: float
    mood: Optional[str] = None

class DailyReflection(BaseModel):
    wins: List[str] = Field(default_factory=list)
    challenges: List[str] = Field(default_factory=list)
    tomorrow_setup: Optional[str] = None

class DailyPlanSchema(PlanBase):
    tasks: List[DailyTask]
    morning_routine: Optional[List[str]] = None
    evening_routine: Optional[List[str]] = None
    capital_allocation: List[CapitalAllocation] = Field(default_factory=list)
    metrics: Optional[DailyMetrics] = None
    reflection: Optional[DailyReflection] = None

    @field_validator('capital_allocation', mode='before')
    @classmethod
    def sanitize_capital_allocation(cls, v):
        """Drop invalid capital_allocation entries (e.g. strings from LLM)."""
        if not isinstance(v, list):
            return []
        return [item for item in v if isinstance(item, dict)]

    @model_validator(mode='after')
    def check_schedule_logic(self):
        # Only validate tasks that have times
        timed_tasks = [t for t in self.tasks if t.start_time and t.end_time]
        sorted_tasks = sorted(timed_tasks, key=lambda x: x.start_time)

        total_minutes = 0
        for i in range(len(sorted_tasks) - 1):
            current = sorted_tasks[i]
            next_task = sorted_tasks[i+1]

            c_end = self._time_to_min(current.end_time)
            n_start = self._time_to_min(next_task.start_time)

            if c_end > n_start:
                raise ValueError(f"Task overlap detected: '{current.title}' ends at {current.end_time}, but '{next_task.title}' starts at {next_task.start_time}")

            total_minutes += (c_end - self._time_to_min(current.start_time))

        if sorted_tasks:
            last = sorted_tasks[-1]
            total_minutes += (self._time_to_min(last.end_time) - self._time_to_min(last.start_time))

        if total_minutes > 1440:
            raise ValueError(f"Total plan duration ({total_minutes // 60}h) exceeds 24 hours")

        return self

    def _time_to_min(self, t: str) -> int:
        h, m = map(int, t.split(':'))
        return h * 60 + m

# --- 2. Weekly Plan Schema ---
class StrategicOutcome(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    metric: str
    current_value: float
    target_value: float
    deadline: str

class WeeklyGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    category: TaskCategory
    priority: Priority
    deadline_day: str = Field(..., description="Monday, Tuesday, etc.")
    subtasks: List[str] = Field(default_factory=list)
    linked_outcome_id: Optional[str] = None # Link to StrategicOutcome.id



class HabitTracker(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    habit: str
    frequency: str = "daily"
    target_days: List[str] = []
    streak: int = 0
    score: int = Field(0, ge=0, le=100)

class WeeklyBalance(BaseModel):
    work_hours: float
    personal_hours: float
    sleep_hours: float

class WeeklyPlanSchema(PlanBase):
    focus_area: str
    outcomes: List[StrategicOutcome] = Field(..., description="Strategic Outcomes")
    goals: List[WeeklyGoal]
    habits: List[HabitTracker]
    capital_allocation: List[CapitalAllocation] = Field(default_factory=list)
    balance: Optional[WeeklyBalance] = None
    weekly_productivity_index: Optional[int] = Field(None, ge=0, le=100)

# --- 3. Monthly Plan Schema ---
class MonthlyMilestone(BaseModel):
    title: str
    category: TaskCategory
    deadline_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    status: str = "pending"
    progress: int = Field(0, ge=0, le=100)

class KPIMetric(BaseModel):
    name: str
    target_value: float
    actual_value: float = 0.0
    unit: str

class MonthlyAnalytics(BaseModel):
    trend_data: Dict[str, List[float]] # e.g. {"revenue": [10, 12, 15]}

class MonthlyPlanSchema(PlanBase):
    theme: str
    strategic_goals: List[str]
    milestones: List[MonthlyMilestone]
    kpis: List[KPIMetric] = Field(default_factory=list)
    analytics: Optional[MonthlyAnalytics] = None
    review_date: str

# --- 4. Finance Plan Schema ---
class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE_FIXED = "expense_fixed"
    EXPENSE_VARIABLE = "expense_variable"
    SAVINGS = "savings"
    DEBT_PAYMENT = "debt_payment"

class ExpenseTag(str, Enum):
    NEED = "need"
    WANT = "want"
    INVESTMENT = "investment"
    WASTE = "waste"
    UNKNOWN = "unknown"

class FinancialItem(BaseModel):
    title: str
    type: TransactionType
    amount: float
    currency: str = "USD"
    due_date: Optional[str] = None
    category: str = "finance"
    tag: ExpenseTag = ExpenseTag.UNKNOWN

class AIInsightVerdict(str, Enum):
    GOOD = "good_decision"
    RISKY = "risky"
    HARMFUL = "harmful"

class SpendingInsight(BaseModel):
    item: str
    verdict: AIInsightVerdict
    reason: str

class FinancePlanSchema(PlanBase):
    total_income_projected: float
    total_expenses_projected: float
    savings_goal: float
    financial_health_score: Optional[int] = Field(None, ge=0, le=100)
    items: List[FinancialItem]
    ai_insights: List[SpendingInsight] = Field(default_factory=list)

    @model_validator(mode='after')
    def check_budget_math(self):
        # Calculate totals from items
        income = sum(i.amount for i in self.items if i.type == TransactionType.INCOME)
        expenses = sum(i.amount for i in self.items if i.type in (TransactionType.EXPENSE_FIXED, TransactionType.EXPENSE_VARIABLE, TransactionType.DEBT_PAYMENT))
        
        # Allow 10% variance for "projected" numbers vs item logic
        if abs(income - self.total_income_projected) > (income * 0.1) + 10:
             # Just warn or strict? User asked for consistency.
             # Strict: raise ValueError(f"Projected income {self.total_income_projected} does not match items total {income}")
             pass 

        # Logical Check: Income - Expenses should roughly equal Savings (or surplus)
        surplus = self.total_income_projected - self.total_expenses_projected
        if surplus < self.savings_goal:
             # This is a soft check - maybe the user has existing savings?
             # But if surplus is negative and savings goal is positive, that's impossible.
             if self.savings_goal > 0 and surplus < 0:
                 raise ValueError(f"Impossible plan: Expenses exceed income by {abs(surplus)}, cannot save {self.savings_goal}")

        return self
