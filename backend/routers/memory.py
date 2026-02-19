"""
LifeOS Memory Router — User Memory CRUD with Security
=======================================================
Manages user memories with ownership verification, input
validation, and singleton RAG manager integration.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from beanie import PydanticObjectId
from datetime import datetime
from models import User, UserMemory, MemoryTier
from routers.auth import get_current_user
from rag.manager import get_rag_manager
from utils.logger import get_logger
from utils.security import validate_object_id, MAX_MEMORY_CONTENT_LENGTH
from utils.validators import validate_memory_content

log = get_logger("router.memory")

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/", response_model=List[UserMemory])
async def get_memories(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    query = UserMemory.find(UserMemory.user_id == current_user.id)
    if category:
        query = query.find(UserMemory.category == category)
    return await query.to_list()


@router.post("/", response_model=UserMemory)
async def add_memory(
    content: str = Body(..., embed=True),
    category: str = Body("preference", embed=True),
    current_user: User = Depends(get_current_user),
):
    # Validate input
    try:
        content = validate_memory_content(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate category
    valid_categories = {"constraint", "preference", "goal", "pattern"}
    if category not in valid_categories:
        category = "preference"

    memory = UserMemory(
        user_id=current_user.id,
        content=content,
        category=category,
        source="manual",
        tier=MemoryTier.LONG_TERM,  # Manual additions are permanent
        confidence=1.0,
    )
    await memory.insert()

    # Sync to RAG index
    try:
        rag = get_rag_manager()
        rag.add_memory(content)
    except Exception as exc:
        log.warning(f"RAG sync failed (non-blocking): {exc}")

    log.info(f"Memory added manually: user={current_user.id}, category={category}")
    return memory


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
):
    mid = validate_object_id(memory_id)
    memory = await UserMemory.get(mid)

    if not memory or memory.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Memory not found")

    await memory.delete()
    log.info(f"Memory deleted: id={mid}")

    return {"status": "deleted"}
