"""
LifeOS Profile Router — User Profile CRUD with Validation
===========================================================
Manages user profile settings with time format validation,
input sanitization, and structured logging.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from models import User, UserProfile
from routers.auth import get_current_user
from utils.logger import get_logger
from utils.security import sanitize_string, validate_time_string

log = get_logger("router.profile")

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileBase(BaseModel):
    work_start_time: str = Field(..., pattern=r'^([01]\d|2[0-3]):([0-5]\d)$')
    work_end_time: str = Field(..., pattern=r'^([01]\d|2[0-3]):([0-5]\d)$')
    sleep_time: str = Field(..., pattern=r'^([01]\d|2[0-3]):([0-5]\d)$')
    wake_time: str = Field(..., pattern=r'^([01]\d|2[0-3]):([0-5]\d)$')
    energy_levels: str = Field(..., max_length=200)
    health_goals: Optional[str] = Field(None, max_length=500)
    learning_goals: Optional[str] = Field(None, max_length=500)
    finance_goals: Optional[str] = Field(None, max_length=500)
    role: Optional[str] = Field(None, max_length=50)
    constraints: Optional[str] = Field(None, max_length=1000)


@router.get("/")
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    profile = await UserProfile.find_one(UserProfile.user_id == current_user.id)
    return profile


@router.post("/")
@router.put("/")
async def update_profile(
    request: ProfileBase,
    current_user: User = Depends(get_current_user),
):
    log.info(f"Profile update: user={current_user.id}")
    try:
        payload = request.model_dump()

        # Sanitize string fields
        for key in ("health_goals", "learning_goals", "finance_goals", "constraints"):
            if payload.get(key):
                payload[key] = sanitize_string(payload[key], 1000)

        profile = await UserProfile.find_one(UserProfile.user_id == current_user.id)

        if profile:
            for key, value in payload.items():
                setattr(profile, key, value)
            await profile.save()
        else:
            profile = UserProfile(user_id=current_user.id, **payload)
            await profile.insert()

        log.info(f"Profile saved: user={current_user.id}")
        return {"success": True}

    except Exception as e:
        log.error(f"Profile update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Profile update failed")
