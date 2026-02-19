"""
LifeOS Chat Router — Message handling with structured error recovery
====================================================================
Manages chat sessions, delegates to ChatbotAgent, and triggers
Memory Agent extraction as a background task.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from models import User, ChatSession, ChatMessage
from utils.validators import validate_chat_message
from ai_orchestrator import AIOrchestrator
from agents.chatbot_agent import ChatbotAgent
from routers.auth import get_current_user
from utils.logger import get_logger, timed

log = get_logger("router.chat")

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


@router.post("/message")
async def chat_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    import time
    start = time.perf_counter()
    log.info(f"Chat request from user={current_user.id}: '{request.message[:50]}'")

    # 1. Manage Session
    chat_session = None
    if request.session_id:
        try:
            sid = PydanticObjectId(request.session_id)
            chat_session = await ChatSession.get(sid)
            if chat_session and chat_session.user_id != current_user.id:
                log.warning(f"Unauthorized access to session {sid} by user {current_user.id}")
                chat_session = None # Cheat: Treat as if it doesn't exist, forcing new session
        except Exception:
            log.debug(f"Invalid session_id '{request.session_id}' — creating new session")

    if not chat_session:
        chat_session = ChatSession(
            user_id=current_user.id,
            title=request.message[:30] + "...",
            created_at=datetime.utcnow(),
            messages=[],
        )
        await chat_session.insert()
        log.info(f"New chat session created: {chat_session.id}")

    # 2. Save User Message
    user_msg = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow(),
    )
    chat_session.messages.append(user_msg)
    await chat_session.save()

    # 3. Agent Processing (with error boundary)
    try:
        orchestrator = AIOrchestrator()
        context = await orchestrator.assemble_payload(current_user.id, request.message)

        agent = ChatbotAgent(context, rag_manager=orchestrator.rag_manager)
        response = await agent.send_message(current_user.id, request.message)
    except Exception as exc:
        log.error(f"Agent processing failed: {exc}", exc_info=True)
        response = {
            "reply": "I apologize — I encountered an issue processing your request. Please try again.",
            "actions": [],
            "clarification_questions": [],
        }

    # 4. Save Assistant Response
    if response.get("type") == "ACTION_RESPONSE":
        ai_msg = ChatMessage(
            role="assistant",
            content=response.get("message", ""),
            timestamp=datetime.utcnow(),
            questions=[],
            actions=[response.get("action")] if response.get("action") else [],
        )
    else:
        # Legacy / Error Fallback
        ai_msg = ChatMessage(
            role="assistant",
            content=response.get("reply", ""),
            timestamp=datetime.utcnow(),
            questions=response.get("clarification_questions", []),
            actions=response.get("actions", []),
        )

    chat_session.messages.append(ai_msg)
    await chat_session.save()
    
    # Enrich the response for frontend consumption (legacy compat or strict?)
    # Frontend expects message object or just the response dict?
    # The original returned `response` dict directly.
    # The frontend uses `chatStore` which likely uses the API response directly.
    # If I return the raw `ACTION_RESPONSE` dict, the frontend needs to handle it.
    
    # We should return the stored message structure? 
    # Or just return the raw response if it's ACTION_RESPONSE?
    
    # Original:
    # response["session_id"] = str(chat_session.id)
    # return response

    response["session_id"] = str(chat_session.id)

    # 5. Background Memory Extraction
    try:
        from agents.memory_agent import MemoryAgent
        memory_agent = MemoryAgent(orchestrator.rag_manager)
        background_tasks.add_task(memory_agent.extract_and_save, current_user.id, request.message)
    except Exception as exc:
        log.warning(f"Memory agent scheduling failed (non-blocking): {exc}")

    elapsed = (time.perf_counter() - start) * 1000
    log.info(f"Chat response delivered in {elapsed:.0f}ms")

    return response


@router.get("/history")
async def get_chat_history_legacy(
    current_user: User = Depends(get_current_user),
):
    return []
