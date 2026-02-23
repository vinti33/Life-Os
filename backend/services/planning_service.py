"""
LifeOS Planning Service — Hierarchy & Aggregation Logic
=======================================================
Handles cross-plan logic, including:
- Progress rollback (Daily -> Weekly -> Monthly)
- Plan linking (Parent/Child relationships)
- Budget aggregation for Finance plans
"""

from typing import Optional, List, Dict, Any
from datetime import date, timedelta, datetime
from beanie import PydanticObjectId
from models import Plan, Task, PlanType, PlanStatus, TaskStatus
from utils.logger import get_logger

log = get_logger("service.planning")

class PlanningService:
    @staticmethod
    async def get_active_or_create(user_id: PydanticObjectId, plan_type: PlanType, ref_date: date = None) -> Plan:
        """
        Fetches the active plan for the given type and date. 
        Creates a draft if none exists.
        """
        if not ref_date:
            ref_date = date.today()
            
        # Determine start/end date based on plan type
        # For simplicity, we stick to the provided date as the anchor
        # In real logic, we'd calculate Week Start/End or Month Start/End
        
        plan = await Plan.find_one(
            Plan.user_id == user_id,
            Plan.plan_type == plan_type,
            Plan.date == str(ref_date) # Simplified date matching
        )
        
        if not plan:
            log.info(f"Creating new {plan_type} plan for user {user_id} on {ref_date}")
            plan = Plan(
                user_id=user_id,
                plan_type=plan_type,
                date=str(ref_date),
                status=PlanStatus.DRAFT
            )
            await plan.insert()
            
        return plan

    @staticmethod
    async def create_daily_plan(user_id: PydanticObjectId, date_str: str, context: str = "") -> Plan:
        """
        Generates a new daily plan using the AI Orchestrator.
        """
        from ai_orchestrator import AIOrchestrator
        orchestrator = AIOrchestrator()
        
        # Note: AIOrchestrator currently defaults to today's date. 
        # Future TODO: Pass date_str to orchestrator.
        plan, _ = await orchestrator.generate_plan_draft(user_id, context, PlanType.DAILY)
        return plan

    @staticmethod
    async def link_plans(child_plan_id: PydanticObjectId, parent_plan_id: PydanticObjectId):
        """Links a child plan (Daily) to a parent plan (Weekly)."""
        child = await Plan.get(child_plan_id)
        if child:
            child.parent_plan_id = parent_plan_id
            await child.save()
            log.info(f"Linked plan {child_plan_id} -> {parent_plan_id}")

    @staticmethod
    async def calculate_progress(plan_id: PydanticObjectId) -> float:
        """
        Recalculates completion percentage for a plan based on its tasks.
        Updates the plan in DB and returns the value.
        """
        plan = await Plan.get(plan_id)
        if not plan:
            return 0.0

        tasks = await Task.find(Task.plan_id == plan.id).to_list()
        if not tasks:
            return 0.0
            
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        
        progress = (completed / total) * 100.0 if total > 0 else 0.0
        
        if plan.progress != progress:
            plan.progress = progress
            await plan.save()
            log.debug(f"Updated plan {plan.id} progress: {progress:.1f}%")
            
            # Recursive Rollup
            if plan.parent_plan_id:
                await PlanningService.calculate_progress(plan.parent_plan_id)
                
        return progress

    @staticmethod
    async def get_hierarchy_context(user_id: PydanticObjectId, current_type: PlanType) -> str:
        """
        Retrieves context from higher-level plans to guide the AI.
        Daily -> Needs Weekly Context
        Weekly -> Needs Monthly Context
        """
        context_parts = []
        
        if current_type == PlanType.DAILY:
            # Fetch active Weekly Plan
            # Logic to find "current week" plan needed
            # For now, just find *latest* active weekly plan
            weekly = await Plan.find(
                Plan.user_id == user_id,
                Plan.plan_type == PlanType.WEEKLY,
                Plan.status == PlanStatus.ACTIVE
            ).sort(-Plan.date).first_or_none()
            
            if weekly:
                context_parts.append(f"WEEKLY GOALS: {weekly.summary}")
                tasks = await Task.find(Task.plan_id == weekly.id).to_list()
                for t in tasks:
                    context_parts.append(f"- {t.title} (Priority {t.priority})")

        return "\n".join(context_parts)

    @staticmethod
    async def calculate_finance_summary(plan_id: PydanticObjectId) -> Dict[str, Any]:
        """
        Aggregates financial data for a Finance Plan.
        Returns total expenses, remaining budget, and alerts.
        """
        plan = await Plan.get(plan_id)
        if not plan or plan.plan_type != PlanType.FINANCE:
            return {}

        tasks = await Task.find(Task.plan_id == plan.id).to_list()
        
        # Assume metadata holds 'budget'
        total_budget = float(plan.metadata.get("budget", 0.0))
        
        # Aggregate logic: 
        # For simplicity in MVP, all tasks in Finance Plan are transactions.
        # If amount < 0 => Expense. If amount > 0 => Income.
        # Wait, usually UI enters positive numbers for expense. 
        # Let's check 'metadata' for 'type' or just sum all amounts?
        # Let's standardise: All amounts are positive. Expenses are 'transaction' type.
        
        total_active_expenses = sum(t.amount for t in tasks if t.amount and t.task_type == "transaction")
        
        remaining = total_budget - total_active_expenses
        status = "on_track"
        if remaining < 0:
            status = "over_budget"
        elif remaining < (total_budget * 0.1):
            status = "warning"
            
        summary = {
            "total_budget": total_budget,
            "total_spent": total_active_expenses,
            "remaining": remaining,
            "status": status
        }
        
        # Update plan metadata
        plan.metadata.update(summary)
        await plan.save()
        
        return summary
    @staticmethod
    async def apply_safety_checks(plan_id: PydanticObjectId, user_id: PydanticObjectId):
        """
        Enforces schedule integrity on an entire plan.
        1. Fetches all tasks.
        2. Fixes overlaps and enforces work locks.
        3. Persists changes and syncs with external services.
        """
        from models import User
        user = await User.get(user_id)
        if not user or not plan_id:
            return
            
        # 1. Fetch Plan & Tasks
        plan = await Plan.get(plan_id)
        if not plan: return
        
        tasks = await Task.find(Task.plan_id == plan_id).to_list()
        if not tasks: return

        # 2. Extract Profile Info (Simplified)
        # In a real app, we'd fetch the Profile model
        from models import UserProfile
        profile_obj = await UserProfile.find_one(UserProfile.user_id == user_id)
        profile = {
            "role": profile_obj.role if profile_obj else "Other",
            "work_start_time": profile_obj.work_start_time if profile_obj else "09:00",
            "work_end_time": profile_obj.work_end_time if profile_obj else "17:00",
        }

        # 3. Convert to dicts for agent logic
        task_dicts = []
        for t in tasks:
            d = t.dict()
            d["id"] = str(t.id) # Preserve ID for comparison
            task_dicts.append(d)

        # 4. Resolve Overlaps & Locks
        from agents.planner_agent import fix_overlaps, enforce_work_school_lock
        
        # Sort by start time first to ensure fix_overlaps works correctly
        from agents.planner_agent import time_to_minutes
        task_dicts.sort(key=lambda x: time_to_minutes(x.get("start_time", "00:00")))
        
        # Apply logic
        fixed_tasks = enforce_work_school_lock(task_dicts, profile)
        fixed_tasks = fix_overlaps(fixed_tasks)

        # 5. Persist Changes
        from services.calendar_service import CalendarService
        cal = CalendarService()
        
        # Create indexed map for fast lookup
        original_map = {str(t.id): t for t in tasks}
        
        for fixed in fixed_tasks:
            tid_str = fixed.get("id")
            if not tid_str: continue # Skip new tasks (shouldn't happen here)
            
            orig = original_map.get(tid_str)
            if not orig: continue
            
            # Check if times changed
            changed = (
                orig.start_time != fixed["start_time"] or 
                orig.end_time != fixed["end_time"]
            )
            
            if changed:
                log.info(f"Self-Healing: Updating {orig.title} to {fixed['start_time']}-{fixed['end_time']}")
                orig.start_time = fixed["start_time"]
                orig.end_time = fixed["end_time"]
                await orig.save()
                
                # Sync with External Calendar
                await cal.update_event(orig.id, orig.start_time, orig.end_time)

        log.info(f"Schedule integrity check complete for plan {plan_id}")

    @staticmethod
    async def ensure_daily_plan(user_id: PydanticObjectId, date_str: str) -> Optional[Plan]:
        """
        Ensures a daily plan exists for the given date.
        If missing, attempts to auto-generate it from active RoutineTemplates.
        """
        from models import Plan, Task, RoutineTemplate, PlanStatus, PlanType
        
        # 1. Check for existing plan
        plan = await Plan.find_one(
            Plan.user_id == user_id,
            Plan.plan_type == PlanType.DAILY,
            Plan.date == date_str
        )
        
        if plan:
            return plan
            
        # 2. No plan exists - Check for RoutineTemplate
        # Parse weekday: Monday=0, Sunday=6
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = dt.weekday()
        except Exception:
            log.warning(f"Failed to parse date string {date_str} - skipping auto-plan")
            return None
            
        template = await RoutineTemplate.find_one(
            RoutineTemplate.user_id == user_id,
            RoutineTemplate.is_active == True,
            RoutineTemplate.days_of_week == weekday
        )
        
        if not template:
            log.debug(f"No active template found for user {user_id} on weekday {weekday}")
            return None
            
        # 3. Create Plan from Template
        log.info(f"Auto-generating {date_str} plan for user {user_id} from template: {template.name}")
        
        new_plan = Plan(
            user_id=user_id,
            date=date_str,
            plan_type=PlanType.DAILY,
            status=PlanStatus.APPROVED, # Auto-approved if from template
            summary=f"Automated Plan: {template.name}"
        )
        await new_plan.insert()
        
        # 4. Populate Tasks
        tasks_to_insert = []
        for t_data in template.tasks:
            tasks_to_insert.append(Task(
                plan_id=new_plan.id,
                title=t_data.get("title", "Untitled Task"),
                category=t_data.get("category", "other"),
                start_time=t_data.get("start_time"),
                end_time=t_data.get("end_time"),
                priority=t_data.get("priority", 3),
                energy_required=t_data.get("energy_required", "medium"),
                estimated_duration=t_data.get("estimated_duration"),
                metrics=t_data.get("metrics", {}),
                metadata=t_data.get("metadata", {})
            ))
            
        if tasks_to_insert:
            await Task.insert_many(tasks_to_insert)
            log.info(f"Auto-populated {len(tasks_to_insert)} tasks for plan {new_plan.id}")
            
        return new_plan
