from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from beanie import PydanticObjectId
from models import User, ChatSession
from routers.auth import get_current_user

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/sessions")
async def get_sessions(
    current_user: User = Depends(get_current_user)
):
    """List all chat sessions for the user, newest first."""
    sessions = await ChatSession.find(
        ChatSession.user_id == current_user.id
    ).sort(-ChatSession.created_at).to_list()
    
    # Convert ObjectIds to strings for JSON
    result = []
    for s in sessions:
        result.append({
            "id": str(s.id),
            "title": s.title,
            "created_at": s.created_at
        })
    return result

@router.post("/sessions")
async def create_session(
    title: str = "New Chat",
    current_user: User = Depends(get_current_user)
):
    """Explicitly create a new session."""
    new_session = ChatSession(
        user_id=current_user.id, 
        title=title,
        created_at=datetime.utcnow(),
        messages=[]
    )
    await new_session.insert()
    return {"id": str(new_session.id), "title": new_session.title}

@router.get("/sessions/{session_id}")
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get full message history for a specific session."""
    try:
        sid = PydanticObjectId(session_id)
        chat_session = await ChatSession.get(sid)
    except:
         raise HTTPException(status_code=400, detail="Invalid Session ID")

    if not chat_session or chat_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return {"session": chat_session, "messages": chat_session.messages}
