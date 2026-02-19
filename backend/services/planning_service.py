"""
LifeOS Planning Service — Hierarchy & Aggregation Logic
=======================================================
Handles cross-plan logic, including:
- Progress rollback (Daily -> Weekly -> Monthly)
- Plan linking (Parent/Child relationships)
- Budget aggregation for Finance plans
"""

from typing import Optional, List, Dict, Any
from datetime import date, timedelta
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
