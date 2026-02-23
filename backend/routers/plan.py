"""
LifeOS Plan Router — Plan lifecycle management
================================================
Endpoints for generating, approving, rejecting, and
retrieving daily plans. Integrated with structured logging.
"""

import time as time_mod
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator
from beanie import PydanticObjectId
from models import User, Plan, Task, PlanStatus, PlanType, TaskStatus
from ai_orchestrator import AIOrchestrator
from routers.auth import get_current_user
from utils.logger import get_logger

log = get_logger("router.plan")

router = APIRouter(prefix="/plan", tags=["plan"])


class PlanRequest(BaseModel):
    context: str = Field(default="Plan my day", max_length=500)
    plan_type: PlanType = Field(default=PlanType.DAILY)
    
    @field_validator('plan_type', mode='before')
    @classmethod
    def case_insensitive_plan_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.lower()
        return v


@router.post("/generate")
async def generate_plan(
    request: PlanRequest,
    current_user: User = Depends(get_current_user),
):
    start = time_mod.perf_counter()
    log.info(f"Plan generation requested: user={current_user.id}, type={request.plan_type}, context='{request.context[:50]}'")

    # 1. Validation Checks
    if not request.context.strip():
        raise HTTPException(status_code=400, detail="Context cannot be empty.")

    # 2. Dependency Initialization
    try:
        orchestrator = AIOrchestrator()
    except Exception as e:
        log.error(f"Orchestrator initialization failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Planning service is temporarily unavailable (Component Init Failed).")

    # 3. Orchestrator Call
    try:
        plan, clarification_questions = await orchestrator.generate_plan_draft(
            current_user.id, request.context, plan_type=request.plan_type
        )
    except ValueError as ve:
        # Business logic errors from orchestrator (e.g. empty inputs)
        log.warning(f"Orchestrator input validation error: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        # LLM or internal pipeline failures
        log.error(f"Plan generation pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate plan due to an internal AI error.")

    # 4. Result Validation (Defensive Null Checks)
    if not plan:
        log.error("Orchestrator returned None for plan object")
        raise HTTPException(status_code=500, detail="Internal Error: Plan generation yielded no result.")
    
    if not plan.id:
        log.error(f"Generated plan has no persistence ID. Plan data: {plan}")
        raise HTTPException(status_code=500, detail="Internal Error: Plan was not saved to database.")

    # 5. Task Retrieval (Safe)
    try:
        tasks = await Task.find(Task.plan_id == plan.id).sort(+Task.start_time).to_list()
    except Exception as e:
        log.error(f"Failed to retrieve tasks for plan {plan.id}: {e}", exc_info=True)
        # We raise 500 here because the plan was created but we can't show it.
        # This prevents the frontend from receiving a broken plan object.
        raise HTTPException(status_code=500, detail="Plan created but failed to retrieve tasks from database.")

    # 6. Plan Linking (Hierarchy)
    try:
        from services.planning_service import PlanningService
        # Logic to find parent
        # For Daily, find active Weekly. For Weekly, find active Monthly.
        parent_type = {
            PlanType.DAILY: PlanType.WEEKLY,
            PlanType.WEEKLY: PlanType.MONTHLY
        }.get(request.plan_type)
        
        if parent_type:
             parent = await Plan.find(
                Plan.user_id == current_user.id,
                Plan.plan_type == parent_type,
                Plan.status == PlanStatus.ACTIVE
            ).sort(-Plan.date).first_or_none()
             
             if parent:
                 await PlanningService.link_plans(plan.id, parent.id)

    except Exception as exc:
        log.warning(f"Failed to link plan to parent (non-blocking): {exc}")

    elapsed = (time_mod.perf_counter() - start) * 1000
    log.info(f"Plan generated successfully: plan_id={plan.id}, tasks={len(tasks)}, elapsed={elapsed:.0f}ms")

    return {
        "plan_id": str(plan.id),
        "version": plan.version,
        "summary": plan.summary,
        "tasks": tasks,
        "clarification_questions": clarification_questions,
        # Flatten metadata into the response for frontend convenience
        "outcomes": plan.metadata.get("outcomes", []),
        "capital_allocation": plan.metadata.get("capital_allocation", []),
        "habits": plan.metadata.get("habits", []),
        "metadata": plan.metadata,
    }


@router.post("/approve")
async def approve_plan(
    plan_id: str,
    version: int = None,
    current_user: User = Depends(get_current_user),
):
    try:
        pid = PydanticObjectId(plan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Plan ID")

    plan = await Plan.get(pid)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Optimistic Lock Check
    if version is not None and plan.version != version:
        raise HTTPException(status_code=409, detail="Plan has been modified by another process")

    plan.status = PlanStatus.APPROVED
    plan.version += 1
    await plan.save()
    log.info(f"Plan approved: plan_id={pid}")

    # Trigger Calendar Sync (non-blocking failure)
    try:
        from services.calendar_service import CalendarService
        cal = CalendarService()
        await cal.sync_plan(plan.id)
    except Exception as exc:
        log.warning(f"Calendar sync failed (non-blocking): {exc}")

    return {"status": "approved"}


@router.post("/reject")
async def reject_plan(
    plan_id: str,
    version: int = None,
    current_user: User = Depends(get_current_user),
):
    try:
        pid = PydanticObjectId(plan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Plan ID")

    plan = await Plan.get(pid)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Optimistic Lock Check
    if version is not None and plan.version != version:
        raise HTTPException(status_code=409, detail="Plan has been modified by another process")

    await plan.delete()
    log.info(f"Plan rejected and deleted: plan_id={pid}")
    return {"status": "rejected"}


@router.get("/active")
async def get_active_plan(
    plan_type: PlanType = PlanType.DAILY,
    current_user: User = Depends(get_current_user),
):
    query = [
        Plan.user_id == current_user.id,
        Plan.plan_type == plan_type
    ]
    
    if plan_type == PlanType.DAILY:
        from services.planning_service import PlanningService
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Autonomous Plan Injection
        await PlanningService.ensure_daily_plan(current_user.id, today_str)
        
        query.append(Plan.date == today_str)

    plan = await Plan.find(*query).sort(-Plan.id).first_or_none()

    if not plan:
        return {"plan_id": None, "tasks": []}

    tasks = await Task.find(Task.plan_id == plan.id).sort(Task.start_time).to_list()
    
    # Initialize default status (since it's removed from model)
    for task in tasks:
        task.status = TaskStatus.PENDING # Default

    # Merge per-date completion status
    if plan.date:
        from models import TaskCompletion
        completions = await TaskCompletion.find(
            TaskCompletion.user_id == current_user.id,
            TaskCompletion.date == plan.date
        ).to_list()
        
        # Create map: task_id -> status
        status_map = {str(c.task_id): c.status for c in completions}
        
        # Overlay completion status
        for task in tasks:
            if str(task.id) in status_map:
                task.status = status_map[str(task.id)]

    return {
        "plan_id": str(plan.id),
        "version": plan.version,
        "status": plan.status,
        "summary": plan.summary,
        "date": plan.date,
        "plan_type": plan.plan_type,
        "metadata": plan.metadata,
        "outcomes": plan.metadata.get("outcomes", []),
        "capital_allocation": plan.metadata.get("capital_allocation", []),
        "habits": plan.metadata.get("habits", []),
        "tasks": tasks,
    }


@router.post("/edit")
async def edit_plan(
    request: PlanRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Edit the current active plan based on a chat instruction.
    Unlike /generate (which always creates a fresh plan), /edit:
      1. Fetches the existing active plan's tasks
      2. Passes them as 'current_plan' context to the LLM
      3. The LLM modifies the plan according to the user's request
      4. Old tasks are deleted and replaced with the new tasks in-place
    """
    start = time_mod.perf_counter()
    log.info(f"Plan EDIT requested: user={current_user.id}, type={request.plan_type}, context='{request.context[:60]}'")

    # 1. Find current active plan
    plan = await Plan.find(
        Plan.user_id == current_user.id,
        Plan.plan_type == request.plan_type,
    ).sort(-Plan.id).first_or_none()

    if not plan:
        log.info("No active plan found for edit — delegating to generate")
        return await generate_plan(request, current_user)

    # 2. Load current tasks as edit context
    current_tasks = await Task.find(Task.plan_id == plan.id).sort(Task.start_time).to_list()
    current_tasks_dicts = [
        {
            "id": str(t.id),
            "title": t.title,
            "category": t.category if isinstance(t.category, str) else t.category.value,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "priority": t.priority if isinstance(t.priority, int) else (t.priority.value if hasattr(t.priority, "value") else 1),
        }
        for t in current_tasks
    ]

    # 3. Call planning strategy with existing tasks as context
    try:
        from planning.daily_strategy import DailyStrategy
        from ai_orchestrator import AIOrchestrator

        orchestrator = AIOrchestrator()
        payload = await orchestrator.assemble_payload(current_user.id, request.context, request.plan_type)
        profile = payload.get("profile", {})

        strategy = DailyStrategy(
            llm_client=orchestrator.planner,
            rag_manager=orchestrator.rag_manager,
        )
        plan_data = await strategy.generate(
            profile=profile,
            context=request.context,
            stats=payload.get("stats", []),
            patterns=payload.get("patterns", []),
            current_plan=current_tasks_dicts,
        )
    except Exception as exc:
        log.error(f"Plan edit generation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to edit plan. Please try again.")

    new_tasks = plan_data.get("tasks", [])
    if not new_tasks:
        raise HTTPException(status_code=422, detail="The AI could not determine how to modify your plan.")

    # 4. Replace tasks in DB (delete old, insert new)
    await Task.find(Task.plan_id == plan.id).delete()

    tasks_to_insert = []
    for t in new_tasks:
        if isinstance(t, dict):
            title = t.get("title", "Task")
            category = t.get("category", "other")
            start_time = t.get("start_time")
            end_time = t.get("end_time")
            priority = t.get("priority", 2)
            task_type = t.get("task_type", "task")
        else:
            title = t.title
            category = t.category.value if hasattr(t.category, "value") else t.category
            start_time = t.start_time
            end_time = t.end_time
            priority = t.priority.value if hasattr(t.priority, "value") else t.priority
            task_type = "task"

        tasks_to_insert.append(Task(
            plan_id=plan.id,
            title=title,
            category=category,
            start_time=start_time,
            end_time=end_time,
            priority=priority,
            task_type=task_type,
            status="pending",
        ))

    await Task.insert_many(tasks_to_insert)

    # 5. Update plan summary & version
    plan.summary = plan_data.get("plan_summary", plan.summary)
    plan.version = plan.version + 1
    await plan.save()

    elapsed = (time_mod.perf_counter() - start) * 1000
    log.info(f"Plan edited: plan_id={plan.id}, tasks={len(tasks_to_insert)}, elapsed={elapsed:.0f}ms")

    saved_tasks = await Task.find(Task.plan_id == plan.id).sort(Task.start_time).to_list()
    return {
        "plan_id": str(plan.id),
        "version": plan.version,
        "summary": plan.summary,
        "tasks": saved_tasks,
        "clarification_questions": plan_data.get("clarification_questions", []),
    }
