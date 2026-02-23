"""
LifeOS Task Router — Task CRUD with Ownership Verification
============================================================
Endpoints for creating, updating, rescheduling tasks.
All mutating operations verify ownership via the plan → user chain.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from models import User, Task, TaskStatus, PlanStatus
from routers.auth import get_current_user
from utils.logger import get_logger
from utils.security import verify_task_ownership, validate_object_id, validate_time_string

log = get_logger("router.task")

router = APIRouter(prefix="/task", tags=["task"])


class UpdateTaskRequest(BaseModel):
    task_id: str
    status: TaskStatus
    reason: Optional[str] = Field(None, max_length=500)
    completion_date: Optional[str] = None # YYYY-MM-DD for recurring/plan-based completion


class RescheduleRequest(BaseModel):
    task_id: str
    new_start_time: str
    new_end_time: Optional[str] = None


@router.post("/update")
async def update_task(
    request: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
):
    tid = validate_object_id(request.task_id)

    # Ownership check: task → plan → user
    await verify_task_ownership(tid, current_user.id)

    task = await Task.get(tid)
    
    # STRICT: Always use TaskCompletion. If no date provided, default to today.
    # The user requested removing 'completed' from Task, so we MUST store status in TaskCompletion.
    completion_date = request.completion_date
    if not completion_date:
        from datetime import date
        completion_date = str(date.today())

    from models import TaskCompletion
    
    # Upsert TaskCompletion record
    completion = await TaskCompletion.find_one(
        TaskCompletion.task_id == tid,
        TaskCompletion.date == completion_date
    )
    
    if completion:
        completion.status = request.status
        await completion.save()
    else:
        completion = TaskCompletion(
            task_id=tid,
            user_id=current_user.id,
            date=completion_date,
            status=request.status
        )
        await completion.insert()
        
    log.info(f"Task completion updated: id={tid}, date={completion_date}, status={request.status}")

    # Trigger Tracker Agent on completion (only if DONE)
    if request.status == TaskStatus.DONE:
        try:
            from agents.tracker_agent import TrackerAgent
            tracker_agent = TrackerAgent()
            # Note: We might want to pass date to tracker agent in future
            await tracker_agent.log_completion(task)
        except Exception as exc:
            log.warning(f"Tracker agent failed (non-blocking): {exc}")

    # Trigger Progress Rollup (Hierarchy)
    try:
        from services.planning_service import PlanningService
        await PlanningService.calculate_progress(task.plan_id)
    except Exception as exc:
        log.warning(f"Progress rollup failed (non-blocking): {exc}")

    return {"success": True}


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    start_time: str
    end_time: str
    category: str = "other"


@router.post("/create")
async def create_task(
    request: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
):
    from models import Plan
    from datetime import date

    log.info(f"Task create: user={current_user.id}, title='{request.title[:30]}'")

    # Validate time formats
    if not validate_time_string(request.start_time) or not validate_time_string(request.end_time):
        raise HTTPException(status_code=400, detail="Invalid time format (expected HH:MM)")

    today_str = str(date.today())
    plan = await Plan.find(Plan.user_id == current_user.id).sort(-Plan.id).first_or_none()

    if not plan:
        plan = Plan(
            user_id=current_user.id,
            date=today_str,
            status=PlanStatus.DRAFT,
            summary="Auto-created by task addition",
        )
        await plan.insert()
        log.info(f"Auto-created plan {plan.id} for task addition")

    task = Task(
        plan_id=plan.id,
        title=request.title,
        category=request.category,
        start_time=request.start_time,
        end_time=request.end_time,
        priority=2,
        # status removed from here
    )
    await task.insert()

    log.info(f"Task created: id={task.id}")
    
    # Trigger Self-Healing Overlap Prevention
    from services.planning_service import PlanningService
    await PlanningService.apply_safety_checks(plan.id, current_user.id)
    
    return {"success": True, "task": task}





@router.post("/reschedule")
async def reschedule_task(
    request: RescheduleRequest,
    current_user: User = Depends(get_current_user),
):
    log.info(f"Reschedule request: task={request.task_id}")
    tid = validate_object_id(request.task_id)

    # Ownership check
    await verify_task_ownership(tid, current_user.id)

    from agents.calendar_agent import CalendarAgent
    calendar_agent = CalendarAgent()

    task = await Task.get(tid)

    # Calculate end time if missing (preserve original duration)
    end_time = request.new_end_time
    if not end_time:
        def parse_minutes(t):
            h, m = map(int, t.split(":"))
            return h * 60 + m

        def format_minutes(m):
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}"

        try:
            duration = parse_minutes(task.end_time) - parse_minutes(task.start_time)
            new_start_min = parse_minutes(request.new_start_time)
            end_time = format_minutes(new_start_min + duration)
        except Exception:
            end_time = request.new_start_time
            log.warning("Failed to calculate end time — using start time as fallback")

    try:
        result = await calendar_agent.reschedule_task(
            tid, request.new_start_time, end_time
        )
        log.info(f"Task rescheduled: id={tid} → {request.new_start_time}-{end_time}")
        
        # Trigger Self-Healing Overlap Prevention
        from services.planning_service import PlanningService
        await PlanningService.apply_safety_checks(task.plan_id, current_user.id)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/today")
async def get_today_tasks(
    current_user: User = Depends(get_current_user),
):
    return []
