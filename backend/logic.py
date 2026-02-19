from datetime import date, datetime, timedelta
from typing import Optional
from sqlmodel import Session, select, func
from models import (
    User, Plan, Task, TaskStatus, Feedback, 
    Pattern, LongTermProgress, PlanStatus
)

class LifeOSLogic:
    def __init__(self, session: Session):
        self.session = session

    def update_task_status(self, task_id: int, status: TaskStatus, reason: Optional[str] = None):
        """
        Updates task status and tracks failure patterns if missed.
        """
        task = self.session.get(Task, task_id)
        if not task:
            return None
        
        old_status = task.status
        task.status = status
        if reason:
            task.reason_if_missed = reason
            
        # Pattern Recognition Logic
        if status == TaskStatus.MISSED:
            plan = self.session.get(Plan, task.plan_id)
            pattern = self.session.exec(
                select(Pattern).where(
                    Pattern.user_id == plan.user_id,
                    Pattern.task_type == task.category,
                    Pattern.failed_time_slot == task.start_time
                )
            ).first()
            
            if pattern:
                pattern.failure_count += 1
            else:
                pattern = Pattern(
                    user_id=plan.user_id,
                    task_type=task.category,
                    failed_time_slot=task.start_time,
                    failure_count=1
                )
                self.session.add(pattern)
        
        self.session.commit()
        return task

    def run_end_of_day_job(self, user_id: int, target_date: date):
        """
        Calculates daily stats, updates streaks, and checks for upgrades.
        """
        plan = self.session.exec(
            select(Plan).where(Plan.user_id == user_id, Plan.date == target_date)
        ).first()
        
        if not plan:
            return None
            
        tasks = self.session.exec(select(Task).where(Task.plan_id == plan.id)).all()
        total = len(tasks)
        completed = len([t for t in tasks if t.status == TaskStatus.DONE])
        missed = len([t for t in tasks if t.status == TaskStatus.MISSED])
        
        success_rate = (completed / total * 100) if total > 0 else 0
        
        # Save Feedback
        feedback = Feedback(
            plan_id=plan.id,
            total_tasks=total,
            completed_tasks=completed,
            missed_tasks=missed,
            success_percentage=success_rate
        )
        self.session.add(feedback)
        
        # Update Streaks
        progress = self.session.exec(
            select(LongTermProgress).where(LongTermProgress.user_id == user_id)
        ).first()
        
        if not progress:
            progress = LongTermProgress(user_id=user_id)
            self.session.add(progress)
            
        if success_rate >= 80: # Threshold for streak
            progress.current_streak_days += 1
        else:
            progress.current_streak_days = 0
            progress.last_break_date = target_date
            
        # Upgrade Eligibility (e.g., 30 days of 90%+ success)
        # Simplified: Check if streak > 30 and average success > 90
        if progress.current_streak_days >= 30:
            progress.eligible_for_upgrade = True
            
        plan.status = PlanStatus.COMPLETED
        self.session.commit()
        
        return feedback
