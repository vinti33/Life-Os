from typing import List
from models import Plan, Task, PlanStatus
from beanie import PydanticObjectId

class CalendarService:
    def __init__(self):
        # Removed session
        pass

    async def create_event(self, task_id: PydanticObjectId):
        """Creates a calendar event for a specific task."""
        task = await Task.get(task_id)
        if not task:
            return None
        # In a real app, logic for Google Calendar API (google-api-python-client) goes here
        print(f"DEBUG: Created Google Calendar event for Task {task.id}: {task.title}")
        return f"event_{task.id}" # Simulated event ID

    async def update_event(self, task_id: PydanticObjectId, new_start, new_end):
        """Updates an existing calendar event."""
        task = await Task.get(task_id)
        print(f"DEBUG: Updated Google Calendar event for Task {task.id} to {new_start}-{new_end}")
        return True

    async def delete_event(self, task_id: PydanticObjectId):
        """Deletes a calendar event."""
        print(f"DEBUG: Deleted Google Calendar event for Task {task_id}")
        return True

    async def sync_plan(self, plan_id: PydanticObjectId):
        """Pushes all approved tasks of a plan to Google Calendar."""
        plan = await Plan.get(plan_id)
        if not plan or plan.status != PlanStatus.APPROVED:
            return False
        
        tasks = await Task.find(Task.plan_id == plan_id).to_list()
        for task in tasks:
            await self.create_event(task.id)
        
        print(f"DEBUG: Synced Plan {plan_id} with Google Calendar")
        return True
