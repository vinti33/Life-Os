from fastapi import APIRouter, Depends
from models import User, LongTermProgress
from routers.auth import get_current_user

router = APIRouter(prefix="/plan/upgrade", tags=["upgrade"])

@router.get("/eligible")
async def check_upgrade_eligibility(
    current_user: User = Depends(get_current_user)
):
    progress = await LongTermProgress.find_one(LongTermProgress.user_id == current_user.id)
    
    return {"eligible": progress.eligible_for_upgrade if progress else False}

@router.post("/")
def apply_upgrade(
    plan_id: int,
    current_user: User = Depends(get_current_user)
):
    # This would involve an AI call to "Upgrade" the plan
    # based on the 30-60 day consistent performance.
    return {
        "new_plan_id": plan_id, # Placeholder
        "tasks": [],
        "msg": "Upgrade applied successfully"
    }
