from fastapi import APIRouter, Depends
from models import User, Plan, Task, PlanStatus, PlanType
from routers.auth import get_current_user
from typing import Dict, Any, List

router = APIRouter(prefix="/metrics", tags=["metrics"])

# --- Helper Query ---
async def _get_plan_and_tasks(user_id, plan_type):
    plan = await Plan.find(
        Plan.user_id == user_id,
        Plan.plan_type == plan_type
    ).sort(-Plan.id).first_or_none()
    
    if not plan:
        return None, []
        
    tasks = await Task.find(Task.plan_id == plan.id).to_list()
    return plan, tasks

# --- 1. Daily Metrics ---
@router.get("/daily")
async def get_daily_metrics(current_user: User = Depends(get_current_user)):
    try:
        plan, tasks = await _get_plan_and_tasks(current_user.id, PlanType.DAILY)
        if not plan:
            return {"progress": 0, "productivity_score": 0, "completed": 0, "total": 0}
            
        total = len(tasks)

        # Initialize default status for all tasks
        for task in tasks:
            task.status = "pending"

        # Merge per-date completion status (Fix for Recurring Tasks)
        if plan and plan.date:
            from models import TaskCompletion
            completions = await TaskCompletion.find(
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.date == plan.date
            ).to_list()
            
            status_map = {str(c.task_id): c.status for c in completions}
            
            for task in tasks:
                if str(task.id) in status_map:
                    task.status = status_map[str(task.id)]

        completed = sum(1 for t in tasks if t.status == "done")
        progress = (completed / total * 100) if total > 0 else 0
        
        # Simple Productivity Score: Base on completion + high priority weight
        score = 0
        if total > 0:
            dataset = []
            for t in tasks:
                weight = {1: 3, 2: 2, 3: 1, 4: 0.5, 5: 0}.get(t.priority, 1)
                val = 1 if t.status == "done" else 0
                dataset.append(val * weight)
            
            max_possible = sum({1: 3, 2: 2, 3: 1, 4: 0.5, 5: 0}.get(t.priority, 1) for t in tasks)
            score = (sum(dataset) / max_possible * 100) if max_possible > 0 else 0
            
        return {
            "progress": round(progress),
            "productivity_score": round(score),
            "completed": completed,
            "total": total,
            "energy_level": (plan.metadata or {}).get("metrics", {}).get("energy_avg", "Medium")
        }
    except Exception as e:
        # log.error(f"Error calculating daily metrics: {e}") # Ensure logger is imported or use print
        print(f"Error calculating daily metrics: {e}")
        return {"progress": 0, "productivity_score": 0, "completed": 0, "total": 0, "energy_level": "Medium"}

# --- 2. Weekly Metrics ---
@router.get("/weekly")
async def get_weekly_metrics(current_user: User = Depends(get_current_user)):
    try:
        plan, tasks = await _get_plan_and_tasks(current_user.id, PlanType.WEEKLY)
        if not plan:
            return {"goal_progress": 0, "habits_streak": 0}
            
        # Initialize default status
        for task in tasks:
            if not hasattr(task, "status"):
                 task.status = "pending"

        # Goals are stored as tasks with task_type="goal" (normalized by Orchestrator)
        goals = [t for t in tasks if t.task_type == "goal"]
        total = len(goals)
        completed = sum(1 for g in goals if g.status == "done")
        progress = (completed / total * 100) if total > 0 else 0
        
        return {
            "goal_progress": round(progress),
            "total_goals": total,
            "completed_goals": completed,
            "outcomes": (plan.metadata or {}).get("outcomes", [])
        }
    except Exception as e:
        print(f"Error calculating weekly metrics: {e}")
        return {"goal_progress": 0, "total_goals": 0, "completed_goals": 0, "outcomes": []}

# --- 3. Monthly Metrics ---
@router.get("/monthly")
async def get_monthly_metrics(current_user: User = Depends(get_current_user)):
    try:
        plan, tasks = await _get_plan_and_tasks(current_user.id, PlanType.MONTHLY)
        if not plan:
            return {"milestone_progress": 0, "kpi_health": 0}
            
        milestones = [t for t in tasks if t.task_type == "milestone"]
        total = len(milestones)
        # Milestones might use 'progress' field (0-100) instead of binary status
        avg_progress = sum(m.progress for m in milestones) / total if total > 0 else 0
        
        return {
            "milestone_progress": round(avg_progress),
            "active_theme": (plan.metadata or {}).get("theme", "No Theme")
        }
    except Exception as e:
        print(f"Error calculating monthly metrics: {e}")
        return {"milestone_progress": 0, "active_theme": "No Theme"}

# --- 4. Finance Metrics ---
@router.get("/finance")
async def get_finance_metrics(current_user: User = Depends(get_current_user)):
    try:
        plan, tasks = await _get_plan_and_tasks(current_user.id, PlanType.FINANCE)
        if not plan:
            return {"health_score": 0, "savings_rate": 0}
            
        income = sum(t.amount for t in tasks if t.financial_data.get("type") == "income")
        expenses = sum(t.amount for t in tasks if t.financial_data.get("type") in ["expense_fixed", "expense_variable", "debt_payment"])
        
        savings = income - expenses
        savings_rate = (savings / income * 100) if income > 0 else 0
        
        # AI Risk Score (lower is better, so health = 100 - risk)
        # Simple logic: If expense > 80% of income, health drops
        health_score = 100
        if income > 0 and (expenses / income) > 0.8:
            health_score -= 20
        if savings < 0:
            health_score -= 50
            
        return {
            "health_score": max(0, health_score),
            "savings_rate": round(savings_rate, 1),
            "total_income": income,
            "total_expenses": expenses
        }
    except Exception as e:
        print(f"Error calculating finance metrics: {e}")
        return {"health_score": 0, "savings_rate": 0, "total_income": 0, "total_expenses": 0}

# --- 5. LifeOS Index ---
@router.get("/lifeos-index")
async def get_lifeos_index(current_user: User = Depends(get_current_user)):
    try:
        # Aggregates all scores
        d = await get_daily_metrics(current_user)
        w = await get_weekly_metrics(current_user)
        f = await get_finance_metrics(current_user)
        
        # Weighted Formula
        # Productivity (Daily): 40%
        # Strategy (Weekly): 30%
        # Finance: 30%
        
        # Use .get() to safely access keys, defaulting to 0 if missing/failed
        prod_score = d.get("productivity_score", 0)
        strat_score = w.get("goal_progress", 0)
        fin_score = f.get("health_score", 0)
        
        score = (prod_score * 0.4) + (strat_score * 0.3) + (fin_score * 0.3)
        
        return {
            "lifeos_index": round(score),
            "components": {
                "productivity": prod_score,
                "strategy": strat_score,
                "finance": fin_score
            }
        }
    except Exception as e:
        print(f"Error calculating LifeOS index: {e}")
        return {
            "lifeos_index": 0,
            "components": {
                "productivity": 0,
                "strategy": 0,
                "finance": 0
            }
        }
