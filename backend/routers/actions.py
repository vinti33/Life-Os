from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from models import User, Task, Plan, PlanStatus
from routers.auth import get_current_user
from services.planning_service import PlanningService
from agents.calendar_agent import CalendarAgent

from utils.logger import get_logger
from datetime import date

log = get_logger("router.actions")

router = APIRouter(prefix="/chat/action", tags=["actions"])

class ActionDefinition(BaseModel):
    type: str # ADD_TASK, UPDATE_TASK, etc.
    payload: Dict[str, Any]

class ActionWrapper(BaseModel):
    action: ActionDefinition

@router.post("")
async def execute_action(
    wrapper: ActionWrapper,
    current_user: User = Depends(get_current_user),
):
    """
    Execute chatbot actions.
    Expects: { "action": { "type": "...", "payload": {...} } }
    """
    action = wrapper.action
    
    # Log full action object before execution
    log.info(f"Action Request by User {current_user.id}: {action.dict()}")

    if not action.type:
        raise HTTPException(status_code=400, detail="Action type is missing")

    try:
        # Switch-case implementation
        action_type = action.type.upper() # Handle case-insensitivity if needed, but strict is key

        if action_type == "ADD_TASK":
            await _handle_add_task(action.payload, current_user)
            
        elif action_type == "UPDATE_TASK": 
            # Could map to reschedule or generic update
            if "new_start_time" in action.payload:
                 await _handle_reschedule(action.payload, current_user)
            else:
                 # Generic update (status etc)
                 pass

        elif action_type == "DELETE_TASK":
            await _handle_delete_task(action.payload, current_user)

        elif action_type == "CONFIRM_ACTION":
            # Just a confirmation log?
            pass

        elif action_type == "GENERATE_ROUTINE":
            await PlanningService.create_daily_plan(
                current_user.id,
                action.payload.get("date", str(date.today())),
                context=action.payload.get("context", "")
            )
            return {"success": True, "message": "Daily routine generated."}

        elif action_type == "EDIT_PLAN":
            from routers.plan import PlanRequest, edit_plan
            from models import PlanType
            plan_type_str = action.payload.get("plan_type", "daily")
            edit_request = PlanRequest(
                context=action.payload.get("context", "Modify my plan"),
                plan_type=PlanType(plan_type_str),
            )
            result = await edit_plan(edit_request, current_user)
            return {"success": True, "message": "Plan updated.", "plan": result}

        # Fallback for previous 'reschedule' type from agent if not updated yet?
        # We will update agent to send UPDATE_TASK or RESCHEDULE mapped.
        # User list included: ADD_TASK, UPDATE_TASK, DELETE_TASK, CONFIRM_ACTION, GENERATE_ROUTINE.
        # So 'reschedule' should map to UPDATE_TASK? Or I keep 'RESCHEDULE' as internal logic?
        # User list seems strict. Let's map RESCHEDULE logic to UPDATE_TASK if payload has times.
        
        elif action_type == "REPLY":
             # No-op action, just a text response confirmation if needed
             pass

        elif action_type == "RESCHEDULE": # Legacy support or explicit
             await _handle_reschedule(action.payload, current_user)

        else:
            raise HTTPException(status_code=400, detail=f"Invalid action type: {action_type}")

        return {
            "success": True,
            "message": "Action completed successfully"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        log.error(f"Action execution failed: {e}", exc_info=True)
        # Production-ready: Don't leak stack trace to user, but log it.
        raise HTTPException(status_code=500, detail="Internal server error executing action")

# Helper functions to keep main clean

async def _handle_add_task(payload: Dict, user: User):
    title = payload.get("title")
    start_time = payload.get("start_time")
    end_time = payload.get("end_time")
    category = payload.get("category", "other")
    
    if not title or not start_time:
        raise HTTPException(status_code=400, detail="Missing title or start_time for ADD_TASK")

    target_date = payload.get("date", str(date.today()))
    plan = await Plan.find(Plan.user_id == user.id, Plan.date == target_date).first_or_none()
    
    if not plan:
        plan = Plan(
            user_id=user.id,
            date=target_date,
            status=PlanStatus.DRAFT,
            summary="Auto-created by chat action",
        )
        await plan.insert()

    task = Task(
        plan_id=plan.id,
        title=title,
        category=category,
        start_time=start_time,
        end_time=end_time,
        priority=2,
    )
    await task.insert()
    log.info(f"Task created: {task.id}")

async def _handle_reschedule(payload: Dict, user: User):
    task_id = payload.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="Missing task_id for UPDATE_TASK/RESCHEDULE")
        
    calendar_agent = CalendarAgent()
    await calendar_agent.reschedule_task(
        task_id, 
        payload.get("start_time"), 
        payload.get("end_time")
    )
    log.info(f"Task rescheduled: {task_id}")

async def _handle_delete_task(payload: Dict, user: User):
    task_id = payload.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="Missing task_id for DELETE_TASK")

    task = await Task.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Verify the task belongs to this user via its plan
    plan = await Plan.get(task.plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")

    await task.delete()
    log.info(f"Task deleted: {task_id} by user {user.id}")

async def _handle_regenerate_plan(payload: Dict, user: User):
    await PlanningService.create_daily_plan(user.id, payload.get("date", str(date.today())))
    log.info(f"Plan regenerated for user {user.id}")
