"""
LifeOS Planner Agent — Daily Schedule Generator with Retry Logic
================================================================
Generates structured daily plans via LLM, enforces work/school time
locks, implements retry with exponential backoff, and JSON parse recovery.
"""

import json
import re
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import requests
from config import settings
from rag.manager import RAGManager
from models import PlanType
from utils.logger import get_logger, timed, PlannerError

log = get_logger("planner_agent")

# LLM retry configuration
MAX_RETRIES = 1 # Reducing retries to fit in frontend timeout
RETRY_BASE_DELAY_S = 1.0

# Generic requests that skip RAG to save time
_GENERIC_REQUESTS = frozenset([
    "plan my day", "plan today", "what should i do",
    "generate plan", "plan my day today",
])


# ---------------------------------------------------------------------------
# Time Utilities
# ---------------------------------------------------------------------------
def time_to_minutes(t: str) -> int:
    try:
        if not t or ":" not in t: return 0
        h, m = map(int, t.split(":"))
        return h * 60 + m
    except: return 0

def minutes_to_time(m: int) -> str:
    m = max(0, min(m, 1439)) # Cap at 23:59
    h = m // 60
    mm = m % 60
    return f"{h:02d}:{mm:02d}"

def fix_overlaps(tasks: List[Dict[str, Any]], max_minutes: int = 1439) -> List[Dict[str, Any]]:
    """Programmatically resolves overlapping tasks by shifting/shortening."""
    if not tasks: return tasks
    
    # Sort by start time, and then by priority (higher priority first if times same)
    def sort_key(x):
        start = time_to_minutes(x.get("start_time", "00:00"))
        priority = x.get("priority", 3)
        return (start, priority)

    tasks.sort(key=sort_key)
    
    fixed = []
    for i, task in enumerate(tasks):
        curr_start = time_to_minutes(task.get("start_time", "00:00"))
        curr_end = time_to_minutes(task.get("end_time", "00:00"))

        if not fixed:
            # First task must respect boundary
            if curr_start >= max_minutes:
                log.debug(f"Sleep Guard: stripping '{task.get('title')}' - starts after sleep boundary")
                continue
            
            task["end_time"] = minutes_to_time(min(max_minutes, curr_end))
            fixed.append(task)
            continue
            
        prev = fixed[-1]
        prev_end = time_to_minutes(prev.get("end_time", "00:00"))
        
        # If current starts before previous ends, shift it
        if curr_start < prev_end:
            duration = max(15, curr_end - curr_start) # Use 15m as min duration during shift
            new_start = prev_end
            new_end = new_start + duration
            
            # Boundary check: If shifting pushes us into/past sleep boundary
            if new_start >= max_minutes:
                log.debug(f"Sleep Guard: stripping '{task.get('title')}' - pushed beyond boundary")
                continue
                
            task["start_time"] = minutes_to_time(new_start)
            task["end_time"] = minutes_to_time(min(max_minutes, new_end))
            log.debug(f"Safety Shield: shifted '{task.get('title')}' to {task['start_time']}")
        else:
            # Task starts after previous, but check if it's already past boundary
            if curr_start >= max_minutes:
                log.debug(f"Sleep Guard: stripping '{task.get('title')}' - starts after boundary")
                continue
            # Ensure end time doesn't bleed past boundary
            task["end_time"] = minutes_to_time(min(max_minutes, curr_end))
            
        fixed.append(task)
    return fixed


# ---------------------------------------------------------------------------
# Hard Enforcement Layer
# ---------------------------------------------------------------------------
def enforce_work_school_lock(tasks: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Strips non-work tasks from the locked work/school window."""
    role = profile.get("role")
    if role not in ("Working", "Student"):
        return tasks

    try:
        start = time_to_minutes(profile.get("work_start_time"))
        end = time_to_minutes(profile.get("work_end_time"))
    except (ValueError, TypeError):
        log.warning("Invalid work times in profile — skipping enforcement")
        return tasks

    safe_tasks = []
    for task in tasks:
        try:
            t_start = time_to_minutes(task["start_time"])
            t_end = time_to_minutes(task["end_time"])
        except (ValueError, TypeError, KeyError):
            log.warning(f"Task '{task.get('title', '?')}' has invalid times — keeping it")
            safe_tasks.append(task)
            continue

        inside_locked_zone = not (t_end <= start or t_start >= end)

        if not inside_locked_zone:
            safe_tasks.append(task)
            continue

        is_work_task = task.get("category") in ("work", "learning")
        is_break = (
            ("break" in task.get("title", "").lower() or "lunch" in task.get("title", "").lower() or "dinner" in task.get("title", "").lower())
            and task.get("category") in ("personal", "health")
            and (t_end - t_start) <= 90
        )

        if is_work_task or is_break:
            safe_tasks.append(task)
        else:
            log.debug(f"Enforced: stripped '{task.get('title')}' from locked zone")

    return safe_tasks


def enforce_sleep_lock(tasks: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Hard-strips or truncates tasks that exceed the user's sleep boundary."""
    sleep_time_str = profile.get("sleep_time")
    if not sleep_time_str:
        return tasks
        
    try:
        sleep_limit = time_to_minutes(sleep_time_str)
    except (ValueError, TypeError):
        log.warning(f"Invalid sleep_time '{sleep_time_str}' in profile — skipping lock")
        return tasks

    safe_tasks = []
    for task in tasks:
        try:
            t_start = time_to_minutes(task["start_time"])
            t_end = time_to_minutes(task["end_time"])
        except (ValueError, TypeError, KeyError):
            safe_tasks.append(task)
            continue

        # 1. Total strip if task starts after sleep
        if t_start >= sleep_limit:
            log.debug(f"Sleep Guard: stripped '{task.get('title')}' - starts after sleep at {sleep_time_str}")
            continue
            
        # 2. Truncate if task ends after sleep
        if t_end > sleep_limit:
            log.debug(f"Sleep Guard: truncated '{task.get('title')}' at {sleep_time_str}")
            task["end_time"] = minutes_to_time(sleep_limit)
            
        safe_tasks.append(task)

    return safe_tasks


# ---------------------------------------------------------------------------
# JSON Recovery
# ---------------------------------------------------------------------------
def _recover_json(text: str) -> dict | None:
    """Attempts to extract JSON from mixed LLM output (text + JSON)."""
    # Try to find a JSON object in the text
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def _sanitize_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fixes invalid categories, times, and enums from LLM output."""
    valid_categories = {"work", "health", "learning", "finance", "personal", "other"}
    valid_energy = {"high", "medium", "low"}
    
    for task in tasks:
        # 1. Sanitize Category
        cat = str(task.get("category", "other")).lower().strip()
        if "|" in cat:
            cat = cat.split("|")[0].strip()
        
        if cat not in valid_categories:
            if cat in ("social", "socializing", "fun", "entertainment"):
                cat = "personal"
            elif cat in ("transport", "commute", "travel"):
                cat = "other"
            elif cat in ("study", "reading"):
                cat = "learning"
            elif cat in ("gym", "exercise", "meditation"):
                cat = "health"
            elif cat in ("job", "meeting", "email"):
                cat = "work"
            else:
                cat = "other"
        task["category"] = cat

        # 2. Sanitize Priority (Force int 1-5)
        p = task.get("priority", 3)
        if isinstance(p, str):
            p_lower = p.lower()
            if "critical" in p_lower or "1" in p_lower: p = 1
            elif "high" in p_lower or "2" in p_lower: p = 2
            elif "low" in p_lower or "4" in p_lower: p = 4
            elif "optional" in p_lower or "5" in p_lower: p = 5
            else: p = 3
        try:
            p = int(p)
            task["priority"] = max(1, min(5, p))
        except (ValueError, TypeError):
            task["priority"] = 3

        # 3. Sanitize Energy Required (Enum)
        energy = str(task.get("energy_required", "medium")).lower().strip()
        if energy not in valid_energy:
            if "high" in energy: energy = "high"
            elif "low" in energy: energy = "low"
            else: energy = "medium"
        task["energy_required"] = energy

        # 3. Sanitize Times (Handle ints/malformed strings)
        for field in ("start_time", "end_time"):
            val = task.get(field)
            if val is None:
                continue
            
            # Handle integers (e.g. 0 -> "00:00", 900 -> "09:00", 9 -> "09:00")
            if isinstance(val, (int, float)):
                val = int(val)
                if val == 0:
                    val = "00:00"
                elif 0 < val <= 24: # e.g. 9 -> 09:00
                    val = f"{val:02d}:00"
                elif val >= 100: # e.g. 900 -> 09:00
                     h = val // 100
                     m = val % 100
                     val = f"{h:02d}:{m:02d}"
                else:
                    val = None # Discard weird numbers
            
            # Ensure output is string
            if val is not None:
                val = str(val).strip()
                # Basic check for HH:MM format
                if not re.match(r"^\d{2}:\d{2}$", val):
                     # Try to fix simple "9:00" -> "09:00"
                     if re.match(r"^\d{1}:\d{2}$", val):
                         val = "0" + val
                     else:
                         val = None # Invalid format
            
            task[field] = val

    return tasks


# ---------------------------------------------------------------------------
# Planner Agent
# ---------------------------------------------------------------------------
class PlannerAgent:
    def __init__(self, rag_manager: RAGManager | None = None):
        # We use requests + asyncio.to_thread because AsyncOpenAI/httpx 
        # has connectivity issues in this environment (likely IPv6/localhost resolution)
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        self.rag_manager = rag_manager

    async def _call_llm(self, system_prompt: str) -> dict:
        """
        Executes LLM call via requests (sync) wrapped in asyncio.to_thread 
        to bypass httpx/asyncio networking issues.
        """
        def _sync_request():
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": settings.AI_MODEL,
                "messages": [{"role": "system", "content": system_prompt}],
                "temperature": 0.1,
                "max_tokens": 768,
                "options": {
                    "num_predict": 768,
                    "num_ctx": 4096,
                    "stop": ["}"] # Help it stop after JSON
                }
            }
            # 900s (15 mins) timeout per attempt to match frontend
            r = requests.post(url, json=payload, headers=headers, timeout=900)
            r.raise_for_status()
            return r.json()

        return await asyncio.to_thread(_sync_request)

    async def _ping_ollama(self) -> bool:
        """Quickly checks if Ollama is alive."""
        base_url = settings.OPENAI_BASE_URL.replace("/v1", "")
        try:
            def _sync():
                r = requests.get(f"{base_url}/api/tags", timeout=5)
                return r.status_code == 200
            return await asyncio.to_thread(_sync)
        except:
             return False

    @timed("planner_agent")
    async def generate(self, system_prompt: str, response_model: Any) -> Any:
        """
        Generic generation method for strategies using Pydantic.
        """
        # Early exit if Ollama is down to avoid 15min hang
        if not await self._ping_ollama():
             log.error("Ollama service is unresponsive. Aborting generation.")
             raise PlannerError("Local AI service (Ollama) is unavailable or unresponsive.")

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                log.info(f"LLM call attempt {attempt}/{MAX_RETRIES}")
                resp_json = await self._call_llm(system_prompt)
                
                try:
                    raw_content = resp_json["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    raw_content = json.dumps(resp_json)

                # Parse JSON
                try:
                    data = json.loads(raw_content)
                except json.JSONDecodeError:
                    data = _recover_json(raw_content)
                    if data is None:
                        raise PlannerError("LLM returned unparseable output", {"raw": raw_content[:200]})
                
                # Sanitize tasks before validation (only for dict tasks)
                if "tasks" in data and isinstance(data["tasks"], list):
                    data["tasks"] = _sanitize_tasks(
                        [t for t in data["tasks"] if isinstance(t, dict)]
                    )
                    # Apply overlap prevention BEFORE Pydantic validation
                    data["tasks"] = fix_overlaps(data["tasks"])

                # Auto-repair: if data is a list of tasks, wrap it
                if isinstance(data, list):
                    log.warning("LLM returned a list instead of schema — auto-wrapping")
                    # Assume list contains tasks
                    data = {"plan_summary": "Updated plan", "tasks": data}
                    if len(data["tasks"]) > 0 and isinstance(data["tasks"][0], dict):
                         data["tasks"] = _sanitize_tasks(data["tasks"])
                
                # Auto-repair: if data is a single task dict (has title but no tasks key), wrap it
                if isinstance(data, dict) and "tasks" not in data:
                    # Case 1: Single Task
                    if "title" in data:
                        log.warning("LLM returned a single task instead of schema — auto-wrapping")
                        data = {"plan_summary": "Updated plan", "tasks": [data]}
                        data["tasks"] = _sanitize_tasks(data["tasks"])
                    
                    # Case 2: Dict of Tasks (e.g. {"1": {...}, "2": {...}})
                    else:
                        potential_tasks = []
                        for k, v in data.items():
                            if isinstance(v, dict) and ("title" in v or "category" in v):
                                potential_tasks.append(v)
                        
                        if potential_tasks:
                            log.warning(f"LLM returned a dict of {len(potential_tasks)} tasks — auto-wrapping")
                            data = {"plan_summary": "Updated plan", "tasks": potential_tasks}
                            data["tasks"] = _sanitize_tasks(data["tasks"])

                # Validate against Pydantic model
                # NOTE: Overlap prevention is applied in the Strategy (e.g. DailyStrategy)
                # or here if we have profile context. 
                # Since 'generate' is generic, we can't easily fix overlaps without knowing the profile.
                # However, we can at least ensure we return a valid model.
                return response_model(**data)

            except Exception as e:
                last_error = e
                log.warning(f"Attempt {attempt} failed: {e}")
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY_S * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)

        log.error(f"All retries failed: {last_error}")
        # Return empty model or raise
        # For safety, returning a default constructed model might be risky if required fields exist
        # Better to raise and let fallback handle it
        raise last_error

    @timed("planner_agent")
    async def generate_plan(
        self,
        profile: Dict[str, Any],
        stats: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        context: str,
        plan_type: str = "daily",
    ) -> Dict[str, Any]:
        """
        Generates a plan via LLM with retry logic and JSON recovery.
        Falls back to empty plan on total failure.
        """
        # Conditional RAG bypass for generic requests
        should_query_rag = context.strip().lower() not in _GENERIC_REQUESTS
        rag_context = ""
        if self.rag_manager and should_query_rag:
            log.info(f"Querying RAG for specific context: '{context[:50]}'")
            rag_context = self.rag_manager.query(context)

        if plan_type == PlanType.FINANCE:
             system_prompt = self._build_finance_prompt(profile, stats, patterns, context, rag_context)
        elif plan_type == PlanType.WEEKLY:
             system_prompt = self._build_weekly_prompt(profile, stats, patterns, context, rag_context)
        elif plan_type == PlanType.MONTHLY:
             system_prompt = self._build_monthly_prompt(profile, stats, patterns, context, rag_context)
        else:
             system_prompt = self._build_daily_prompt(profile, stats, patterns, context, rag_context)

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                log.info(f"LLM call attempt {attempt}/{MAX_RETRIES}")
                
                # Use robust requests-based call
                resp_json = await self._call_llm(system_prompt)
                
                # Extract content (OpenAI format or Ollama format depending on what endpoint returns)
                # Typically /v1/chat/completions returns standard OpenAI structure
                try:
                    raw_content = resp_json["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                     # Fallback for raw Ollama or different structure
                     raw_content = json.dumps(resp_json)

                # Primary parse
                try:
                    plan = json.loads(raw_content)
                except json.JSONDecodeError:
                    log.warning(f"JSON parse failed on attempt {attempt} — trying recovery")
                    plan = _recover_json(raw_content)
                    if plan is None:
                        raise PlannerError("LLM returned unparseable output", {"raw": raw_content[:200]})

                # Validate minimum structure
                if "tasks" not in plan:
                    plan["tasks"] = []
                if "plan_summary" not in plan:
                    plan["plan_summary"] = "Daily plan"
                if "clarification_questions" not in plan:
                    plan["clarification_questions"] = []

                # Hard enforcement for Daily plans only
                if plan_type == PlanType.DAILY:
                    # 1. Enforce work/school locks
                    plan["tasks"] = enforce_work_school_lock(plan["tasks"], profile)
                    # 2. Enforce sleep lock
                    plan["tasks"] = enforce_sleep_lock(plan["tasks"], profile)
                    # 3. Programmatically fix overlaps with sleep boundary
                    sleep_limit = 1439
                    if profile.get("sleep_time"):
                        try:
                            sleep_limit = time_to_minutes(profile["sleep_time"])
                        except: pass
                    plan["tasks"] = fix_overlaps(plan["tasks"], max_minutes=sleep_limit)
                
                log.info(f"Plan generated ({plan_type}): {len(plan.get('tasks', []))} items")
                return plan

            except PlannerError:
                raise  # Don't retry on parse failures after recovery attempt
            except Exception as e:
                last_error = e
                log.warning(f"Attempt {attempt} failed: {e}")
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY_S * (2 ** (attempt - 1))
                    log.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)

        # All retries exhausted
        log.error(f"All {MAX_RETRIES} attempts failed: {last_error}")
        return {
            "plan_summary": "Plan generation failed",
            "tasks": [],
            "clarification_questions": [
                "The planner service encountered an error. Please try again."
            ],
        }

    def _build_daily_prompt(
        self,
        profile: Dict[str, Any],
        stats: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        context: str,
        rag_context: str,
    ) -> str:
        """Constructs the compressed system prompt for DAILY plan generation."""
        prompt = f"""Strict Daily Scheduler. Generate a realistic plan.
RULES:
1. HIGHEST PRIORITY: User constraints and morning requirements override everything.
2. JSON ONLY. No text outside.
3. Chronological, NO OVERLAPS, no gaps.
4. Min task length = 30m.
5. REQUIRED MEALS: Breakfast (approx 08:00), Lunch (approx 13:00), Dinner (approx 20:00).
6. IF ROLE is "Working" or "Student":
   - Window {profile.get('work_start_time')} to {profile.get('work_end_time')} is LOCKED for work/learning.
   - Only allow breaks (Lunch/Dinner/Short breaks) during this window if they are under 90 mins.
7. First task starts at {profile.get('wake_time')}, last ends at {profile.get('sleep_time')}.

USER PROFILE: {json.dumps(profile)}
STATS: {json.dumps(stats)}
PATTERNS: {json.dumps(patterns)}
KNOWLEDGE: {rag_context}
REQUEST: "{context}"

OUTPUT JSON EXAMPLE:
{{
  "plan_summary": "Productive work day",
  "tasks": [
    {{"title": "Breakfast", "category": "health", "start_time": "08:00", "end_time": "08:30", "priority": 1}},
    {{"title": "Deep Work", "category": "work", "start_time": "09:00", "end_time": "11:00", "priority": 1}},
    {{"title": "Lunch", "category": "personal", "start_time": "13:00", "end_time": "14:00", "priority": 2}}
  ],
  "clarification_questions": []
}}""".strip()
        return prompt

    def _build_weekly_prompt(self, profile, stats, patterns, context, rag_context):
        return f"""Weekly Planner. Generate high-level goals and focus areas for the week.
RULES:
1. Focus on key outcomes, not hourly scheduling.
2. Group tasks by category (Work, Health, Learning).
3. Set realistic priorities.
4. JSON ONLY.

USER PROFILE: {json.dumps(profile)}
REQUEST: "{context}"

OUTPUT JSON EXAMPLE:
{{
  "plan_summary": "Weekly Theme/Focus",
  "tasks": [
    {{"title": "Complete Project X", "category": "work", "priority": 1, "task_type": "goal", "start_time": "Monday", "end_time": "Friday"}}
  ],
  "metadata": {{ "focus_area": "Growth", "habit_tracker": ["Read 30m", "Gym"] }},
  "clarification_questions": []
}}""".strip()

    def _build_monthly_prompt(self, profile, stats, patterns, context, rag_context):
        return f"""Monthly Planner. Strategic overview.
RULES:
1. High-level milestones and deadlines.
2. No daily tasks.
3. JSON ONLY.

REQUEST: "{context}"

OUTPUT JSON EXAMPLE:
{{
  "plan_summary": "Launch Product V2",
  "tasks": [
     {{"title": "Code Freeze", "category": "work", "priority": 1, "task_type": "milestone", "end_time": "2023-10-15"}}
  ],
  "metadata": {{ "theme": "Execution" }},
  "clarification_questions": []
}}""".strip()

    def _build_finance_prompt(self, profile, stats, patterns, context, rag_context):
        return f"""Financial Advisor. Budget and Expense Planning.
RULES:
1. Extract income, expenses, and savings goals.
2. Create transactions or budget items as tasks.
3. JSON ONLY.

REQUEST: "{context}"

OUTPUT JSON EXAMPLE:
{{
  "plan_summary": "Monthly Budget Check",
  "tasks": [
     {{"title": "Rent", "category": "finance", "priority": 1, "task_type": "transaction", "amount": 1500.0, "status": "pending"}}
  ],
  "metadata": {{ "total_budget": 5000.0, "savings_goal": 1000.0, "currency": "USD" }},
  "clarification_questions": []
}}""".strip()

    def ask_clarification(self, profile: Dict[str, Any]) -> List[str]:
        """Returns questions for incomplete profiles."""
        questions = []
        for field in ("wake_time", "sleep_time", "role"):
            if not profile.get(field):
                questions.append(f"What is your {field.replace('_', ' ')}?")
        if profile.get("role") in ("Working", "Student"):
            if not profile.get("work_start_time") or not profile.get("work_end_time"):
                questions.append("What are your work or class start and end times?")
        return questions
