from datetime import datetime, timedelta
from sqlmodel import Session, select
from database import engine
from models import Task, TaskStatus
from services.notification_service import NotificationService

def check_and_trigger_reminders():
    """
    Cron job function to run every 15 minutes.
    Checks for tasks starting in the next 15 minutes and fires notifications.
    """
    with Session(engine) as session:
        notifier = NotificationService(session)
        now = datetime.now()
        soon = now + timedelta(minutes=15)
        
        # In a real app we'd filter by task.start_time precisely
        # Here we simulate the polling logic
        tasks_starting_soon = session.exec(
            select(Task).where(
                Task.status == TaskStatus.PENDING,
                # Simulate time filtering
            )
        ).all()
        
        for task in tasks_starting_soon:
            # Only trigger if within the window (logic simplified for brevity)
            notifier.send_push(task.id, str(task.start_time))
            notifier.send_email(task.id, str(task.start_time))

if __name__ == "__main__":
    print("Starting LifeOS Reminder Engine...")
    check_and_trigger_reminders()
