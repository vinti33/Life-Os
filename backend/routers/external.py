from fastapi import APIRouter, Depends
from pydantic import BaseModel
from models import User
from routers.auth import get_current_user

router = APIRouter(tags=["external"])

class NotificationRequest(BaseModel):
    task_id: int
    type: str # push, email
    time: str

@router.post("/calendar/sync")
def sync_calendar(
    plan_id: int,
    current_user: User = Depends(get_current_user)
):
    # Placeholder for Google Calendar API integration
    # Note: CalendarService usage would need to be instantiated cleanly if used here
    return {"success": True}

@router.post("/notification/send")
def send_notification(
    request: NotificationRequest,
    current_user: User = Depends(get_current_user)
):
    # Placeholder for Email/Push Notification service
    return {"success": True}
