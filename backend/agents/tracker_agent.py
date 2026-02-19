from datetime import date
from beanie import PydanticObjectId
from models import Task, TaskStatus, LongTermProgress

class TrackerAgent:
    def __init__(self):
        pass

    async def log_completion(self, task: Task) -> dict:
        """
        Logs a task completion and updates streaks if applicable.
        """
        print(f"DEBUG: Tracker logging completion for {task.title}")
        
        # Check if all tasks for the plan are done
        # Logic: Find any pending task for this plan
        pending = await Task.find(
            Task.plan_id == task.plan_id,
            Task.status == TaskStatus.PENDING
        ).first_or_none()

        streak_updated = False
        
        # If no pending tasks remain, this was the last one!
        if not pending:
            # We need user_id. Task connects to plan. We can get plan first, or just store user_id in Task?
            # Model Task has plan_id. Plan has user_id.
            from models import Plan
            plan = await Plan.get(task.plan_id)
            if plan:
                streak_updated = await self._update_streak(plan.user_id)
            
        return {
            "task_id": str(task.id),
            "status": "completed",
            "streak_updated": streak_updated
        }

    async def _update_streak(self, user_id: PydanticObjectId) -> bool:
        """
        Updates the user's streak in LongTermProgress.
        """
        progress = await LongTermProgress.find_one(LongTermProgress.user_id == user_id)

        if not progress:
            progress = LongTermProgress(user_id=user_id, current_streak_days=0)
            # Insert happens on save if not exists? No, need insert() for new document usually or save() works if id is None?
            # Beanie: doc = Doc(...); await doc.insert()
            await progress.insert()

        today_str = str(date.today())
        
        # Prevent double counting
        if progress.last_break_date == today_str:
            return False

        # Simple increment logic
        progress.current_streak_days += 1
        progress.last_break_date = today_str
        await progress.save()
        
        print(f"DEBUG: Streak incremented to {progress.current_streak_days}")
        return True
