"""
LifeOS Security Utilities — RBAC, Ownership Guards, Input Sanitization
========================================================================
Provides reusable security primitives for route protection, data access
control, and input cleansing across the LifeOS backend.
"""

import re
import html
from typing import Optional
from functools import wraps
from fastapi import Depends, HTTPException, status
from beanie import PydanticObjectId
from utils.logger import get_logger

log = get_logger("security")

# Max input lengths
MAX_CHAT_MESSAGE_LENGTH = 2000
MAX_PLAN_CONTEXT_LENGTH = 500
MAX_MEMORY_CONTENT_LENGTH = 1000
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254


# ---------------------------------------------------------------------------
# Role-Based Access Control
# ---------------------------------------------------------------------------
def require_role(required_role: str):
    """
    FastAPI dependency that checks the current user has the required role.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_only():
            ...
    """
    from routers.auth import get_current_user
    from models import User

    async def _check(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            log.warning(
                f"RBAC denied: user={current_user.id} has role='{current_user.role}', "
                f"required='{required_role}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check


# ---------------------------------------------------------------------------
# Resource Ownership Verification
# ---------------------------------------------------------------------------
async def verify_plan_ownership(plan_id: PydanticObjectId, user_id: PydanticObjectId) -> bool:
    """Checks that a Plan belongs to the given user."""
    from models import Plan
    plan = await Plan.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.user_id != user_id:
        log.warning(f"Ownership denied: user={user_id} attempted to access plan={plan_id}")
        raise HTTPException(status_code=403, detail="Access denied")
    return True


async def verify_task_ownership(task_id: PydanticObjectId, user_id: PydanticObjectId) -> bool:
    """
    Checks that a Task belongs to the given user via the plan → user chain.
    Returns True if ownership is confirmed, raises HTTPException otherwise.
    """
    from models import Task, Plan
    task = await Task.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    plan = await Plan.get(task.plan_id)
    if not plan or plan.user_id != user_id:
        log.warning(f"Ownership denied: user={user_id} attempted to access task={task_id}")
        raise HTTPException(status_code=403, detail="Access denied")
    return True


async def verify_memory_ownership(memory_id: PydanticObjectId, user_id: PydanticObjectId) -> bool:
    """Checks that a UserMemory belongs to the given user."""
    from models import UserMemory
    memory = await UserMemory.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    if memory.user_id != user_id:
        log.warning(f"Ownership denied: user={user_id} attempted to access memory={memory_id}")
        raise HTTPException(status_code=403, detail="Access denied")
    return True


# ---------------------------------------------------------------------------
# Input Sanitization
# ---------------------------------------------------------------------------
def sanitize_string(text: str, max_length: int = 5000) -> str:
    """
    Sanitizes user input:
    - Strips leading/trailing whitespace
    - Escapes HTML entities to prevent XSS
    - Removes null bytes
    - Truncates to max_length
    """
    if not text:
        return ""
    text = text.strip()
    text = text.replace("\x00", "")  # Remove null bytes
    text = html.escape(text)         # Escape HTML
    return text[:max_length]


def validate_time_string(time_str: str) -> bool:
    """Validates HH:MM format (00:00 to 23:59)."""
    if not time_str:
        return False
    return bool(re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', time_str))


def validate_object_id(id_str: str) -> PydanticObjectId:
    """Safely parses a string to PydanticObjectId, raising HTTP 400 on failure."""
    try:
        return PydanticObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
