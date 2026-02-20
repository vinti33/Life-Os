"""
LifeOS AI Orchestrator — Central Intelligence Pipeline
======================================================
Coordinates data assembly, agent execution, and persistence.
Implements a 3-stage pipeline: Assemble → Generate → Persist
with fallback chains and structured logging.
"""

import json
from datetime import date
from typing import List, Dict, Any, Tuple, Optional
from beanie import PydanticObjectId
from beanie.operators import In
from models import User, UserProfile, Feedback, Pattern, Plan, Task, PlanStatus, PlanType
from agents.planner_agent import PlannerAgent
from agents.review_agent import ReviewAgent
from rag.manager import get_rag_manager
from utils.logger import get_logger, timed, OrchestratorError
from utils.cache import cache

log = get_logger("orchestrator")

# ---------------------------------------------------------------------------
# Agent Registry — extensible pattern for future agents
# ---------------------------------------------------------------------------
_AGENT_REGISTRY: Dict[str, type] = {
    "planner": PlannerAgent,
    "reviewer": ReviewAgent,
}


def register_agent(name: str, cls: type):
    """Register a new agent class by name for dynamic resolution."""
    _AGENT_REGISTRY[name] = cls
    log.info(f"Agent registered: {name} → {cls.__name__}")


class AIOrchestrator:
    """
    Central orchestrator that manages the plan-generation lifecycle.

    Pipeline stages:
        1. ASSEMBLE  — gather profile, stats, patterns, current plan
        2. GENERATE  — invoke planner agent (with fallback on failure)
        3. PERSIST   — save plan + tasks to database
    """

    def __init__(self):
        self.rag_manager = get_rag_manager()
        self.planner = PlannerAgent(rag_manager=self.rag_manager)
        self.reviewer = ReviewAgent()
        log.info("Orchestrator initialized with singleton RAG and agent registry")

    # ------------------------------------------------------------------
    # Stage 1: ASSEMBLE
    # ------------------------------------------------------------------
    @timed("orchestrator")
    @cache(ttl=300, key_prefix="orchestrator:payload")
    async def assemble_payload(self, user_id: PydanticObjectId, context: str, plan_type: PlanType = PlanType.DAILY) -> Dict[str, Any]:
        """Gathers user profile, recent stats, patterns, and current context based on plan type."""
        log.info(f"Assembling payload for user={user_id}, type={plan_type}")

        user = await User.get(user_id)
        profile_obj = await UserProfile.find_one(UserProfile.user_id == user_id)

        # Recent performance (last 7 plans of THIS type)
        recent_plans = await Plan.find(
            Plan.user_id == user_id,
            Plan.plan_type == plan_type
        ).sort(-Plan.date).limit(7).to_list()
        plan_ids = [p.id for p in recent_plans]

        recent_feedback = await Feedback.find(In(Feedback.plan_id, plan_ids)).to_list() if plan_ids else []

        stats_list = []
        for f in recent_feedback:
            p = next((p for p in recent_plans if p.id == f.plan_id), None)
            if p:
                stats_list.append({
                    "date": p.date,
                    "success_rate": f.success_percentage,
                    "completed": f.completed_tasks,
                    "missed": f.missed_tasks,
                })

        # Failure patterns
        patterns_obj = await Pattern.find(Pattern.user_id == user_id).to_list()

        profile = {
            "user_id": str(user_id),
            "work_hours": f"{profile_obj.work_start_time} - {profile_obj.work_end_time}",
            "work_start_time": profile_obj.work_start_time,
            "work_end_time": profile_obj.work_end_time,
            "sleep_wake": f"{profile_obj.sleep_time} - {profile_obj.wake_time}",
            "wake_time": profile_obj.wake_time,
            "sleep_time": profile_obj.sleep_time,
            "health_goals": profile_obj.health_goals,
            "learning_goals": profile_obj.learning_goals,
            "finance_goals": profile_obj.finance_goals,
            "role": profile_obj.role or "Working",
            "constraints": profile_obj.constraints,
        } if profile_obj else {}

        # NEW: Fetch Hierarchy Context (Weekly goals for Daily plan, etc.)
        from services.planning_service import PlanningService
        hierarchy_context = await PlanningService.get_hierarchy_context(user_id, plan_type)
        if hierarchy_context:
            context = f"{hierarchy_context}\n\nUSER REQUEST: {context}"

        # Current active plan tasks
        current_plan_obj = await Plan.find(
            Plan.user_id == user_id,
            Plan.plan_type == plan_type
        ).sort(-Plan.id).first_or_none()
        current_tasks = []
        if current_plan_obj:
            tasks = await Task.find(Task.plan_id == current_plan_obj.id).to_list()
            current_tasks = [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "category": t.category,
                    "priority": t.priority,
                    "task_type": t.task_type,
                    "status": getattr(t, "status", "pending"),
                    "start_time": t.start_time,
                    "end_time": t.end_time,
                    "amount": t.amount,
                    "currency": t.currency,
                    "subtasks": t.subtasks,
                    "metadata": t.metadata,
                    # financial_data and metrics are stored separately in model but often flattened in plan dict
                    # or passed through if needed by strategy
                    "financial_data": t.financial_data,
                    "metrics": t.metrics,
                }
                for t in tasks
            ]

        payload = {
            "profile": profile,
            "current_plan": current_tasks,
            "stats": stats_list,
            "patterns": [
                {
                    "task_type": p.task_type,
                    "failed_time": str(p.failed_time_slot),
                    "suggested_time": str(p.suggested_time_slot),
                    "count": p.failure_count,
                }
                for p in patterns_obj
            ],
            "context": context,
            "plan_type": plan_type,
        }

        log.info(f"Payload assembled: profile={'present' if profile else 'empty'}, stats={len(stats_list)}, patterns={len(patterns_obj)}")
        return payload

    # ------------------------------------------------------------------
    # Stage 2: GENERATE (with fallback)
    # ------------------------------------------------------------------
    @timed("orchestrator")
    async def _generate_with_fallback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempts plan generation via PlannerAgent.
        On failure, returns a minimal safe plan derived from user constraints.
        """
        from planning.factory import PlanningFactory

        try:
            # Use Strategy Pattern
            strategy = PlanningFactory.get_strategy(
                plan_type=payload.get("plan_type", "daily"),
                llm_client=self.planner,  # Reuse self.planner as the LLM client
                rag_manager=self.rag_manager
            )
            
            plan_data = await strategy.generate(
                profile=payload["profile"],
                context=payload["context"],
                stats=payload["stats"],
                patterns=payload["patterns"],
                current_plan=payload.get("current_plan", [])
            )

            tasks = plan_data.get("tasks", [])
            
            # Normalize other plan types into 'tasks' for generic handling
            if not tasks:
                 if plan_data.get("items"): # Finance
                      tasks = plan_data.get("items")
                      # Ensure type is set for Finance items if not present
                      for t in tasks:
                           if "type" not in t and "transaction_type" in t:
                                t["type"] = t["transaction_type"]

                 elif plan_data.get("goals"): # Weekly
                      tasks = plan_data.get("goals")
                      for t in tasks:
                           t["task_type"] = "goal" # Explicitly set type

                 elif plan_data.get("milestones"): # Monthly
                      tasks = plan_data.get("milestones")
                      for t in tasks:
                           t["task_type"] = "milestone"

                 plan_data["tasks"] = tasks

            if not tasks:
                log.warning("Strategy returned zero tasks — triggering fallback")
                return self._build_fallback_plan(payload["profile"], payload.get("current_plan"))

            log.info(f"Strategy generated {len(tasks)} items successfully")
            return plan_data

        except Exception as exc:
            log.error(f"Planning strategy failed: {exc}", exc_info=True)
            return self._build_fallback_plan(payload["profile"], payload.get("current_plan"))

    # @cache removed to avoid async wrapper issues on sync function
    def _build_fallback_plan(self, profile: Dict[str, Any], current_plan: List[Dict] = None) -> Dict[str, Any]:
        """Constructs a minimal safe plan when the primary planner fails."""
        if current_plan:
             log.warning("Fallback: Preserving existing plan")
             return {
                 "plan_summary": "Plan unmodified (AI update failed)",
                 "tasks": current_plan,
                 "clarification_questions": ["I encountered an error trying to update the plan. I've kept your existing schedule safe."]
             }

        wake = profile.get("wake_time", "07:00")
        sleep = profile.get("sleep_time", "23:00")
        work_start = profile.get("work_start_time", "09:00")
        work_end = profile.get("work_end_time", "18:00")

        tasks = [
            {"title": "Morning Routine", "category": "health", "start_time": wake, "end_time": work_start, "priority": 2},
            {"title": "Work Block", "category": "work", "start_time": work_start, "end_time": "12:00", "priority": 1},
            {"title": "Lunch Break", "category": "personal", "start_time": "12:00", "end_time": "13:00", "priority": 3},
            {"title": "Work Block (Afternoon)", "category": "work", "start_time": "13:00", "end_time": work_end, "priority": 1},
            {"title": "Evening Wind-down", "category": "personal", "start_time": work_end, "end_time": sleep, "priority": 4},
        ]

        log.warning(f"Fallback plan generated with {len(tasks)} safe tasks")
        return {
            "plan_summary": "Fallback plan — AI planner was unavailable",
            "tasks": tasks,
            "clarification_questions": ["The planner was temporarily unavailable. This is a safe default plan based on your profile."],
        }

    # ------------------------------------------------------------------
    # Stage 3: PERSIST
    # ------------------------------------------------------------------
    @timed("orchestrator")
    async def _persist_plan(self, user_id: PydanticObjectId, plan_data: Dict[str, Any], plan_type: PlanType) -> Tuple[Plan, List[str]]:
        """Saves the generated plan and its tasks to the database."""
        final_summary = plan_data.get("plan_summary")
        final_tasks = plan_data.get("tasks", [])
        final_questions = plan_data.get("clarification_questions", [])

        new_plan = Plan(
            user_id=user_id,
            date=str(date.today()),
            plan_type=plan_type,
            status=PlanStatus.DRAFT,
            summary=final_summary,
            # Capture all extra fields as metadata (excluding already processed ones)
            metadata={k: v for k, v in plan_data.items() if k not in ["tasks", "plan_summary", "clarification_questions", "items", "goals", "milestones"]},
        )
        await new_plan.insert()

        if final_tasks:
            tasks_to_insert = [
                Task(
                    plan_id=new_plan.id,
                    title=t.get("title"),
                    category=t.get("category", "other"),
                    start_time=t.get("start_time"),
                    end_time=t.get("end_time"),
                    priority=t.get("priority", 1),
                    task_type=t.get("task_type", t.get("type", "task")), # Handle 'type' from Finance items
                    status="pending",
                    amount=t.get("amount"),
                    currency=t.get("currency", "USD"),
                    financial_data=t if t.get("type") in ("income", "expense_fixed", "expense_variable", "savings", "debt_payment") else {},
                    subtasks=t.get("subtasks", []),
                    metrics=t.get("metrics") or ({"kpi": t.get("kpi_metric"), "target": t.get("target_value")} if t.get("kpi_metric") else {}),
                    metadata={
                        **t.get("metadata", {}),
                        "linked_outcome_id": t.get("linked_outcome_id"),
                        "recurrence": t.get("recurrence"),
                        "original_data": {k:v for k,v in t.items() if k not in ["title", "category", "start_time", "end_time", "priority", "task_type", "status", "amount", "currency", "subtasks", "type"]}
                    },
                )
                for t in final_tasks
            ]
            await Task.insert_many(tasks_to_insert)
            log.info(f"Persisted plan {new_plan.id} with {len(tasks_to_insert)} tasks")
        else:
            log.warning(f"Persisted plan {new_plan.id} with 0 tasks")

        return new_plan, final_questions

    # ------------------------------------------------------------------
    # Public API: Full Pipeline
    # ------------------------------------------------------------------
    @timed("orchestrator")
    async def generate_plan_draft(self, user_id: PydanticObjectId, context: str, plan_type: PlanType = PlanType.DAILY) -> Tuple[Plan, List[str]]:
        """
        Full 3-stage pipeline: Assemble → Generate → Persist.
        Returns (Plan, clarification_questions).
        """
        log.info(f"=== PLAN PIPELINE START === user={user_id}, type={plan_type}, context='{context[:50]}'")

        # Stage 1: Assemble
        payload = await self.assemble_payload(user_id, context, plan_type)

        # Stage 2: Generate (with fallback)
        plan_data = await self._generate_with_fallback(payload)

        # Stage 3: Persist
        result = await self._persist_plan(user_id, plan_data, plan_type)

        log.info(f"=== PLAN PIPELINE COMPLETE === plan_id={result[0].id}")
        return result
