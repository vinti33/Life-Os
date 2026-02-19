import json
from typing import Dict, Any, List
from .base_strategy import PlanningStrategy
from schemas.plan_schemas import DailyPlanSchema
from utils.logger import get_logger

log = get_logger("planning.daily")

class DailyStrategy(PlanningStrategy):
    """
    Generates a strictly structured daily plan with time blocking.
    """
    async def generate(self, profile: Dict[str, Any], context: str, **kwargs) -> Dict[str, Any]:
        stats = kwargs.get("stats", [])
        patterns = kwargs.get("patterns", [])
        current_plan = kwargs.get("current_plan", [])
        
        # Heuristic: If existing plan is too short (e.g. truncated), treat as fresh generation
        if current_plan and len(current_plan) < 4:
            log.warning(f"Current plan has only {len(current_plan)} tasks — ignoring context to force FRESH generation")
            current_plan = None

        rag_context = await self._query_rag(context)

        system_prompt = self._build_prompt(profile, stats, patterns, context, rag_context, current_plan)

        # Call LLM
        response = await self.llm_client.generate(system_prompt, response_model=DailyPlanSchema)

        # Post-generation quality check: if too few tasks and no current_plan to modify, retry once
        min_required = 6
        if current_plan:
             # Edit: require at least 50% of original tasks to prevent severe truncation
             min_required = max(3, int(len(current_plan) * 0.5))
        if  len(response.tasks) < min_required:
            log.warning(f"Only {len(response.tasks)} tasks generated (min {min_required}) — retrying with stricter prompt")
            retry_prompt = self._build_prompt(profile, stats, patterns, context, rag_context, current_plan, strict=True)
            try:
                response = await self.llm_client.generate(retry_prompt, response_model=DailyPlanSchema)
            except Exception as e:
                log.warning(f"Retry failed: {e} — using original response")

        # Final fallback: if LLM still can't produce enough tasks, use deterministic template
        # Only apply fallback for NEW plans. For EDITS, abort if too short to protect data.
        if not current_plan and len(response.tasks) < min_required:
            log.warning(f"LLM only produced {len(response.tasks)} tasks after retry — using profile-aware fallback schedule")
            fallback_tasks, fallback_summary = self._build_fallback_schedule(profile)
            # Merge: keep any LLM tasks that don't conflict with fallback, or just use fallback
            response.tasks = fallback_tasks
            response.plan_summary = fallback_summary
        
        # Abort Edit if critical loss of tasks
        if current_plan and len(response.tasks) < min_required:
             log.error(f"Edit abandoned: result has only {len(response.tasks)} tasks vs original {len(current_plan)}. Aborting to save data.")
             raise ValueError("The AI could not update the plan safely (too few tasks generated). Please try again with specific instructions.")

        # Enforce Constraints (Work/School Lock)
        response.tasks = self._enforce_locks(response.tasks, profile)

        return response.dict()

    def _build_prompt(self, profile, stats, patterns, context, rag_context, current_plan=None, strict=False):
        current_plan_str = f"\nCURRENT PLAN:\n{json.dumps(current_plan, indent=2)}" if current_plan else ""

        wake = profile.get('wake_time', '07:00')
        sleep = profile.get('sleep_time', '23:00')
        work_start = profile.get('work_start_time', '09:00')
        work_end = profile.get('work_end_time', '17:00')

        if current_plan:
            task_instruction = (
                "TASK: Modify the CURRENT PLAN based on the REQUEST. This is an EDIT, not a new plan.\n"
                "- CRITICAL: Output a valid JSON object with keys 'plan_summary' and 'tasks'. Do NOT return a list.\n"
                "- If asked to 'break down', 'split', or 'expand' a task: REPLACE that single task with 3-6 specific sub-tasks covering the SAME time slot.\n"
                "  Example: 'Morning Routine' 07:00-08:00 becomes: Wake Up 07:00-07:15, Brush Teeth 07:15-07:25, Shower 07:25-07:45, Get Dressed 07:45-07:55, Breakfast 07:55-08:00.\n"
                "- If asked to 'add' something: Insert it at the appropriate time, adjusting adjacent tasks if needed.\n"
                "- If asked to 'remove' something: Delete that task and fill the gap by extending adjacent tasks.\n"
                "- Keep ALL other existing tasks UNCHANGED with their original times.\n"
                "- Output ALL tasks (modified + unchanged) in the tasks array.\n"
                "- CRITICAL: No two tasks can overlap in time.\n"
                "EXAMPLE OUTPUT:\n"
                "{\n"
                '  "plan_summary": "Adjusted morning routine per request",\n'
                '  "tasks": [ ...list of all task objects... ]\n'
                "}"
            )
        else:
            min_tasks = 10 if strict else 8
            task_instruction = (
                f"TASK: Generate a COMPLETE daily schedule from {wake} (wake) to {sleep} (sleep).\n"
                f"- MANDATORY: At least {min_tasks} tasks, each at least 30 minutes, covering the ENTIRE day from {wake} to {sleep}.\n"
                f"- Work block {work_start}-{work_end} must be filled with 'work' or 'learning' category tasks.\n"
                "- Include: morning routine, focused work blocks, lunch, breaks, evening wind-down, sleep prep.\n"
                "- Every task MUST have start_time and end_time in exact HH:MM format (e.g. 07:00, 13:30).\n"
                "- Tasks must be back-to-back with NO gaps and NO overlaps.\n"
                f"- EXAMPLE STRUCTURE: Morning Routine {wake}-{self._add_hours(wake,1)}, then tasks every 30-120min until {sleep}."
            )

        return f"""You are a strict daily life scheduler. Output JSON only. No markdown. No explanation.

HARD RULES (violating any = FAILURE):
1. Output ONLY a single valid JSON object. No text before or after.
2. Every task MUST have: title (string), category (one of: work/health/learning/finance/personal/other), start_time (HH:MM), end_time (HH:MM), priority (integer 1-5).
3. All tasks CHRONOLOGICAL. No overlaps. No gaps > 30 minutes.
4. Minimum task duration: 30 minutes.
5. Work hours {work_start}-{work_end}: only work/learning/lunch tasks allowed.

USER PROFILE: {json.dumps(profile)}
STATS: {json.dumps(stats)}
PATTERNS: {json.dumps(patterns)}{current_plan_str}
KNOWLEDGE: {rag_context}
REQUEST: "{context}"

{task_instruction}

OUTPUT (JSON ONLY — copy this structure exactly):
{{
  "plan_summary": "Productive balanced day",
  "tasks": [
    {{"title": "Wake Up & Morning Routine", "category": "health", "start_time": "{wake}", "end_time": "{self._add_hours(wake, 1)}", "priority": 2, "energy_required": "low", "estimated_duration": 60}},
    {{"title": "Deep Work Block 1", "category": "work", "start_time": "{work_start}", "end_time": "{self._add_hours(work_start, 2)}", "priority": 1, "energy_required": "high", "estimated_duration": 120}},
    {{"title": "Lunch Break", "category": "personal", "start_time": "13:00", "end_time": "14:00", "priority": 3, "energy_required": "low", "estimated_duration": 60}},
    {{"title": "Deep Work Block 2", "category": "work", "start_time": "14:00", "end_time": "{work_end}", "priority": 1, "energy_required": "high", "estimated_duration": 180}},
    {{"title": "Exercise", "category": "health", "start_time": "{work_end}", "end_time": "{self._add_hours(work_end, 1)}", "priority": 2, "energy_required": "high", "estimated_duration": 60}},
    {{"title": "Dinner", "category": "personal", "start_time": "{self._add_hours(work_end, 1)}", "end_time": "{self._add_hours(work_end, 2)}", "priority": 2, "energy_required": "low", "estimated_duration": 60}},
    {{"title": "Evening Wind-down", "category": "personal", "start_time": "{self._add_hours(work_end, 2)}", "end_time": "{self._subtract_hours(sleep, 0)}", "priority": 3, "energy_required": "low", "estimated_duration": 90}}
  ],
  "morning_routine": [],
  "evening_routine": [],
  "capital_allocation": [],
  "clarification_questions": []
}}
"""


    def _build_fallback_schedule(self, profile: Dict[str, Any]):
        """Generates a complete, realistic day schedule from the user profile.
        Used when the LLM fails to produce enough tasks.
        Returns (list_of_task_dicts, summary_string).
        """
        from schemas.plan_schemas import DailyTask
        from models import TaskCategory, EnergyLevel, Priority

        wake = profile.get('wake_time', '07:00')
        sleep = profile.get('sleep_time', '23:00')
        work_start = profile.get('work_start_time', '09:00')
        work_end = profile.get('work_end_time', '17:00')
        role = profile.get('role', 'Other')

        def t(base, add_mins):
            """Add minutes to HH:MM string."""
            h, m = map(int, base.split(':'))
            total = h * 60 + m + add_mins
            total = max(0, min(total, 23 * 60 + 59))
            return f"{total // 60:02d}:{total % 60:02d}"

        tasks = []
        def add(title, category, start, end, priority=3):
            tasks.append(DailyTask(
                title=title,
                category=TaskCategory(category),
                start_time=start,
                end_time=end,
                priority=Priority(priority),
                energy_required=EnergyLevel.MEDIUM,
                estimated_duration=60,
            ))

        # Morning block (wake → work_start)
        add("Wake Up & Morning Routine", "health", wake, t(wake, 30), priority=2)
        add("Breakfast & Coffee", "personal", t(wake, 30), t(wake, 60), priority=3)
        if work_start > t(wake, 60):
            add("Morning Planning", "work", t(wake, 60), work_start, priority=2)

        # Work block (work_start → work_end)
        if role in ("Working", "Student"):
            # morning work
            add("Deep Work Block 1", "work", work_start, t(work_start, 120), priority=1)
            add("Short Break", "health", t(work_start, 120), t(work_start, 135), priority=4)
            add("Deep Work Block 2", "work", t(work_start, 135), "13:00", priority=1)
            add("Lunch Break", "personal", "13:00", "14:00", priority=3)
            add("Afternoon Work", "work", "14:00", t(work_end, -60), priority=1)
            add("Team Sync / Review", "work", t(work_end, -60), work_end, priority=2)
        else:
            add("Focus Session 1", "work", work_start, t(work_start, 120), priority=1)
            add("Lunch", "personal", t(work_start, 120), t(work_start, 180), priority=3)
            add("Focus Session 2", "learning", t(work_start, 180), work_end, priority=2)

        # Evening block (work_end → sleep)
        add("Exercise / Walk", "health", work_end, t(work_end, 60), priority=2)
        add("Dinner", "personal", t(work_end, 60), t(work_end, 90), priority=3)
        add("Personal Time / Reading", "personal", t(work_end, 90), t(work_end, 150), priority=4)
        add("Wind Down & Sleep Prep", "health", t(work_end, 150), sleep, priority=3)

        return tasks, f"Balanced {'workday' if role in ('Working', 'Student') else 'day'} — wake {wake}, sleep {sleep}"

    def _enforce_locks(self, tasks: List[Any], profile: Dict[str, Any]) -> List[Any]:
        role = profile.get("role")
        if role not in ("Working", "Student"):
            return tasks

        try:
            start_time = profile.get("work_start_time", "09:00")
            end_time = profile.get("work_end_time", "17:00")
            start_mins = self._time_to_minutes(start_time)
            end_mins = self._time_to_minutes(end_time)
        except (ValueError, TypeError):
            log.warning("Invalid work times in profile — skipping enforcement")
            return tasks

        safe_tasks = []
        for task in tasks:
            # Handle Pydantic model access
            try:
                t_start = self._time_to_minutes(task.start_time)
                t_end = self._time_to_minutes(task.end_time)
            except (ValueError, TypeError, AttributeError):
                safe_tasks.append(task)
                continue

            # Check overlap
            inside_locked_zone = not (t_end <= start_mins or t_start >= end_mins)

            if not inside_locked_zone:
                safe_tasks.append(task)
                continue

            # Allow Work/Learning and Lunch
            is_work = task.category.value in ("work", "learning") # Enum value access
            is_lunch = (
                "lunch" in task.title.lower() 
                and task.category.value in ("personal", "health")
                and 12 * 60 <= t_start <= 14 * 60
                and (t_end - t_start) <= 60
            )

            if is_work or is_lunch:
                safe_tasks.append(task)
            else:
                log.info(f"Enforced: stripped '{task.title}' from locked zone")

        return safe_tasks

    def _time_to_minutes(self, t: str) -> int:
        try:
            h, m = map(int, t.split(":"))
            return h * 60 + m
        except Exception:
            return 0

    def _add_hours(self, t: str, hours: float) -> str:
        """Add hours to a HH:MM string, returns HH:MM."""
        try:
            h, m = map(int, t.split(":"))
            total = h * 60 + m + int(hours * 60)
            total = min(total, 23 * 60 + 30)  # cap at 23:30
            return f"{total // 60:02d}:{total % 60:02d}"
        except Exception:
            return t

    def _subtract_hours(self, t: str, hours: float) -> str:
        """Subtract hours from a HH:MM string, returns HH:MM."""
        try:
            h, m = map(int, t.split(":"))
            total = max(0, h * 60 + m - int(hours * 60))
            return f"{total // 60:02d}:{total % 60:02d}"
        except Exception:
            return t
