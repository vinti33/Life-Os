from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from beanie import PydanticObjectId
from models import User, RoutineTemplate, Plan, Task
from routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/routine", tags=["Routine"])

class RoutineCreateFromPlanRequest(BaseModel):
    plan_id: str
    name: str # e.g. "Weekday Routine"
    days_of_week: List[int] # 0-6

@router.post("/create_from_plan")
async def create_routine_from_plan(
    request: RoutineCreateFromPlanRequest,
    current_user: User = Depends(get_current_user),
):
    plan = await Plan.get(PydanticObjectId(request.plan_id))
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    tasks = await Task.find(Task.plan_id == plan.id).to_list()
    
    # Filter out completed/deleted? No, routine should capture structure.
    # Convert tasks to dicts suitable for template
    template_tasks = []
    for t in tasks:
        # We exclude specific date/status, keep schedule/metrics
        task_data = {
            "title": t.title,
            "category": t.category,
            "start_time": t.start_time,
            "end_time": t.end_time,
            "priority": t.priority,
            "energy_required": t.energy_required,
            "estimated_duration": t.estimated_duration,
            "metrics": t.metrics,
            "recurrence": "weekly" # Default
        }
        template_tasks.append(task_data)
        
    # Create Template
    template = RoutineTemplate(
        user_id=current_user.id,
        name=request.name,
        days_of_week=request.days_of_week,
        tasks=template_tasks,
        is_active=True
    )
    await template.insert()
    
    return {"message": "Routine created successfully", "routine_id": str(template.id)}

@router.get("/list")
async def list_routines(current_user: User = Depends(get_current_user)):
    routines = await RoutineTemplate.find(RoutineTemplate.user_id == current_user.id).to_list()
    return routines

@router.delete("/{routine_id}")
async def delete_routine(routine_id: str, current_user: User = Depends(get_current_user)):
    routine = await RoutineTemplate.get(PydanticObjectId(routine_id))
    if not routine or routine.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Routine not found")
    await routine.delete()
    return {"message": "Routine deleted"}
