from datetime import datetime, date, time
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any
from beanie import Document, Link, PydanticObjectId
from pydantic import BaseModel, Field, EmailStr
from enum import Enum

# --- Enums ---

class PlanType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    FINANCE = "finance"

class PlanStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class TaskStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    MISSED = "missed"
    RESCHEDULED = "rescheduled"

class TaskType(str, Enum):
    TASK = "task"
    GOAL = "goal"
    MILESTONE = "milestone"
    TRANSACTION = "transaction"
    EVENT = "event"
    BUDGET_ITEM = "budget item"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class EnergyLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Priority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OPTIONAL = 5

class TaskCategory(str, Enum):
    WORK = "work"
    HEALTH = "health"
    LEARNING = "learning"
    FINANCE = "finance"
    PERSONAL = "personal"
    OTHER = "other"

# --- 1. User Identity Layer ---

class User(Document):
    name: str
    email: EmailStr = Field(unique=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.USER)
    timezone: str = "UTC"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # OAuth
    google_access_token: Optional[str] = None
    google_refresh_token: Optional[str] = None
    google_token_expiry: Optional[datetime] = None

    class Settings:
        name = "users"


# --- 2. User Profile Layer ---

class UserProfile(Document):
    user_id: PydanticObjectId # Linking by ID manually or could use Link[User]
    work_start_time: str # Store time as string "HH:MM" for MongoDB simplicity
    work_end_time: str
    sleep_time: str
    wake_time: str
    energy_levels: str 
    health_goals: Optional[str] = None
    learning_goals: Optional[str] = None
    finance_goals: Optional[str] = None
    role: Optional[str] = None # Student, Working, House Free
    constraints: Optional[str] = None
    
    class Settings:
        name = "profiles"

# --- 3. Planning Layer ---

class Task(BaseModel): 
    # Embedded Document in Plan (NoSQL Design Choice)
    # OR Standalone Document?
    # For querying tasks independently (Analytics, Rescheduling), 
    # Standalone is better.
    pass

# Redefine Task as Document for flexibility
class Task(Document):
    plan_id: PydanticObjectId
    title: str
    category: str 
    start_time: Optional[str] = None # HH:MM string
    end_time: Optional[str] = None   # HH:MM string
    priority: int = 1 
    priority: int = 1 
    # status: TaskStatus = Field(default=TaskStatus.PENDING) # DEPRECATED/REMOVED
    task_type: TaskType = Field(default=TaskType.TASK)
    reason_if_missed: Optional[str] = None
    
    # Advanced Tracking
    energy_required: EnergyLevel = Field(default=EnergyLevel.MEDIUM)
    estimated_duration: Optional[int] = None # Minutes
    actual_duration: Optional[int] = None   # Minutes
    
    # Finance specifics
    amount: Optional[float] = None
    currency: str = "USD"
    financial_data: Dict[str, Any] = Field(default_factory=dict) # For detailed Tax/Category info
    
    # Hierarchy & Progress
    parent_id: Optional[PydanticObjectId] = None  # Link to parent task (e.g. Daily Task -> Weekly Goal)
    subtasks: List[Dict[str, Any]] = Field(default_factory=list) # Simple subtask list
    metrics: Dict[str, Any] = Field(default_factory=dict) # KPI tracking
    
    progress: float = 0.0  # 0.0 to 100.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"
    
    class Settings:
        name = "tasks"
        indexes = [
            [("plan_id", 1), ("start_time", 1)],
            # [("plan_id", 1), ("status", 1)], # Status index removed
        ]

class TaskCompletion(Document):
    task_id: PydanticObjectId
    user_id: PydanticObjectId
    date: str  # YYYY-MM-DD
    status: TaskStatus # Serves as "completed" boolean + extra states
    
    class Settings:
        name = "task_completions"
        indexes = [
            [("task_id", 1), ("date", 1)], # Compound index
            [("user_id", 1), ("date", 1)],
        ] # Beanie doesn't support unique=True in this list format directly easily without model reconfiguration or extra key, but this is sufficient for queries. 
        # For unique constraint, we handle in logic or use pymongo index creation if strictly needed.
        # But user requested logic change mostly. I'll stick to logic enforcement.

class Plan(Document):
    user_id: PydanticObjectId
    date: str # Functions as Start Date for non-daily plans
    end_date: Optional[str] = None
    plan_type: PlanType = Field(default=PlanType.DAILY)
    status: PlanStatus = Field(default=PlanStatus.DRAFT)
    summary: Optional[str] = None
    
    # Hierarchy & Progress
    parent_plan_id: Optional[PydanticObjectId] = None # Link Daily -> Weekly
    progress: float = 0.0 # Aggregated completion rate
    
    progress: float = 0.0 # Aggregated completion rate
    
    # Flexible metadata for plan-specific fields (budget, focus_areas, etc.)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # KPIs and Scoring
    score: Optional[float] = Field(None, ge=0, le=100) # LifeOS Index or specific plan score
    
    # versioning
    version: int = 0

    class Settings:
        name = "plans"
        indexes = [
            [("user_id", 1), ("plan_type", 1), ("status", 1)],
            [("user_id", 1), ("score", -1)],
        ]

class RoutineTemplate(Document):
    user_id: PydanticObjectId
    name: str  # e.g. "Morning Routine - Weekdays"
    days_of_week: List[int] = Field(default_factory=list) # 0=Mon, ... 6=Sun
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    # Example task dict:
    # {
    #   "title": "Run",
    #   "category": "health",
    #   "start_time": "06:00",
    #   "end_time": "06:30",
    #   "metrics": {"target": 5, "unit": "km", "type": "count"},
    #   "priority": 1
    # }
    
    is_active: bool = True
    
    class Settings:
        name = "routine_templates"
        indexes = [
            [("user_id", 1), ("days_of_week", 1)],
        ]

# --- 4. Feedback Layer ---

class Feedback(Document):
    plan_id: PydanticObjectId
    total_tasks: int
    completed_tasks: int
    missed_tasks: int
    success_percentage: float
    
    class Settings:
        name = "feedbacks"

# --- 5. Pattern Recognition Layer ---

class Pattern(Document):
    user_id: PydanticObjectId
    task_type: str
    failed_time_slot: Optional[str] = None
    suggested_time_slot: Optional[str] = None
    failure_count: int = 0
    
    class Settings:
        name = "patterns"

# --- 6. Long-Term Progress Layer ---

class LongTermProgress(Document):
    user_id: PydanticObjectId
    current_streak_days: int = 0
    last_break_date: Optional[str] = None # YYYY-MM-DD
    eligible_for_upgrade: bool = False
    
    class Settings:
        name = "progress"

# --- 7. Chat History Layer ---

class ChatMessage(BaseModel):
    # Embedded in Session is efficient for fetching history
    role: str 
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    questions: Optional[List[str]] = []
    actions: Optional[List[dict]] = []

class ChatSession(Document):
    user_id: PydanticObjectId
    title: str = "New Chat"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[ChatMessage] = [] 
    
    class Settings:
        name = "chat_sessions"

# --- 8. Personalized Memory Layer ---

class MemoryTier(str, Enum):
    SHORT_TERM = "short_term"   # Decays over time, pruned if confidence drops
    LONG_TERM = "long_term"     # Permanent, reinforced by repeated mention

class UserMemory(Document):
    user_id: PydanticObjectId
    category: str  # constraint, preference, goal, pattern
    content: str   # The actual fact
    confidence: float = 0.9
    tier: MemoryTier = Field(default=MemoryTier.SHORT_TERM)
    source: str = "chat"  # chat, manual, rule
    access_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_memories"
        indexes = [
            [("user_id", 1), ("category", 1)],
            [("user_id", 1), ("tier", 1), ("confidence", -1)],
        ]

# --- 9. Finance Layer ---

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    INVESTMENT = "investment"
    DEBT_PAYMENT = "debt_payment"

class Transaction(Document):
    user_id: PydanticObjectId
    date: str  # YYYY-MM-DD
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: str  # e.g. "Housing", "Salary", "Food"
    description: Optional[str] = None
    merchant: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_recurring: bool = False
    
    # Metadata for linking to plans/goals
    linked_plan_id: Optional[PydanticObjectId] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "transactions"
        indexes = [
            [("user_id", 1), ("date", -1)],
            [("user_id", 1), ("category", 1)],
            [("user_id", 1), ("type", 1)],
        ]

class Budget(Document):
    user_id: PydanticObjectId
    month: str  # YYYY-MM
    category: str
    amount_limit: float
    is_hard_limit: bool = False  # If true, alert when exceeded
    
    # Metadata
    linked_goal_id: Optional[PydanticObjectId] = None # e.g. Saving for a car
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "budgets"
        indexes = [
            [("user_id", 1), ("month", 1), ("category", 1)],
        ]
