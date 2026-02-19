from datetime import time
from beanie import PydanticObjectId
from models import Task, TaskStatus

class CalendarAgent:
    def __init__(self):
        # No session
        pass

    async def check_availability(self, plan_id: PydanticObjectId, start_time: str, end_time: str, exclude_task_id: PydanticObjectId = None) -> Task | None:
        """
        Checks if a time slot is occupied by another task.
        """
        # String comparison for times works if format is same HH:MM
        query = Task.find(
            Task.plan_id == plan_id,
            Task.start_time < end_time,
            Task.end_time > start_time
        )
        
        if exclude_task_id:
            query = query.find(Task.id != exclude_task_id)
            
        return await query.first_or_none()

    async def reschedule_task(self, task_id: PydanticObjectId, new_start: str, new_end: str) -> dict:
        """
        Reschedules a task and handles conflicts by auto-swapping.
        """
        task = await Task.get(task_id)
        if not task:
            raise ValueError("Task not found")

        # Capture original slot for swapping
        original_start = task.start_time
        original_end = task.end_time

        # Check for conflict
        conflicting_task = await self.check_availability(task.plan_id, new_start, new_end, exclude_task_id=task.id)

        # Apply new time to primary task
        task.start_time = new_start
        task.end_time = new_end
        task.status = TaskStatus.RESCHEDULED
        await task.save()

        swapped_task = None
        if conflicting_task:
            print(f"DEBUG: Conflict! Swapping {conflicting_task.title} to {original_start}-{original_end}")
            conflicting_task.start_time = original_start
            conflicting_task.end_time = original_end
            conflicting_task.status = TaskStatus.RESCHEDULED
            await conflicting_task.save()
            swapped_task = conflicting_task

        # Sync with Calendar Service (External)
        from services.calendar_service import CalendarService
        cal = CalendarService()
        await cal.update_event(task.id, new_start, new_end)
        if swapped_task:
             await cal.update_event(swapped_task.id, original_start, original_end)

        return {
            "success": True,
            "updated_task": task,
            "swapped_task": swapped_task
        }
