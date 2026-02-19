from fastapi import APIRouter, Depends
from beanie import PydanticObjectId
from beanie.operators import In
from models import User, Feedback, Plan
from routers.auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/daily")
async def get_daily_stats(
    current_user: User = Depends(get_current_user)
):
    # Fetch most recent plan to find associated feedback
    # Beanie generic way
    plan = await Plan.find(Plan.user_id == current_user.id).sort(-Plan.id).first_or_none()
    
    if not plan:
        return {"msg": "No stats found"}

    feedback = await Feedback.find_one(Feedback.plan_id == plan.id)
    
    if not feedback:
        return {"msg": "No stats found"}
        
    return {
        "date": plan.date,
        "total_tasks": feedback.total_tasks,
        "completed_tasks": feedback.completed_tasks,
        "missed_tasks": feedback.missed_tasks,
        "success_percentage": feedback.success_percentage
    }

@router.get("/history")
async def get_stats_history(
    current_user: User = Depends(get_current_user)
):
    # Get last 30 plans
    plans = await Plan.find(Plan.user_id == current_user.id).sort(-Plan.date).limit(30).to_list()
    
    if not plans:
        return []
        
    plan_ids = [p.id for p in plans]
    feedbacks = await Feedback.find(In(Feedback.plan_id, plan_ids)).to_list()
    
    result = []
    for f in feedbacks:
        # Match plan to get date
        p = next((p for p in plans if p.id == f.plan_id), None)
        if p:
            result.append({
                "date": p.date, 
                "success_percentage": f.success_percentage
            })
            
    return result
