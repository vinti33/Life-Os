"""
LifeOS Agent I/O Validators — Input/Output Validation Framework
================================================================
Validates data flowing into and out of AI agents to prevent
malformed or unsafe execution flows.
"""

import re
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

log = get_logger("validators")

# Valid categories for tasks
VALID_CATEGORIES = frozenset({"health", "work", "learning", "finance", "personal", "other"})

# Time format pattern
_TIME_PATTERN = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')

# Max lengths
MAX_TASK_TITLE_LENGTH = 200
MAX_PLAN_SUMMARY_LENGTH = 500


def validate_time_format(t: str) -> bool:
    """Validates HH:MM format string (00:00 to 23:59)."""
    if not t or not isinstance(t, str):
        return False
    return bool(_TIME_PATTERN.match(t.strip()))


def validate_plan_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and sanitizes plan output from the Planner Agent.
    Ensures required fields exist, times are valid, categories are known.
    Returns the cleaned plan data.
    """
    if not isinstance(data, dict):
        log.warning("Plan output is not a dict — returning empty plan")
        return {"plan_summary": "Invalid plan output", "tasks": [], "clarification_questions": []}

    # Ensure required fields
    if "plan_summary" not in data or not data["plan_summary"]:
        data["plan_summary"] = "Daily plan"

    if "tasks" not in data or not isinstance(data["tasks"], list):
        data["tasks"] = []

    if "clarification_questions" not in data:
        data["clarification_questions"] = []

    # Validate each task
    valid_tasks = []
    for i, task in enumerate(data["tasks"]):
        if not isinstance(task, dict):
            log.warning(f"Task {i} is not a dict — skipping")
            continue

        # Required fields
        if "title" not in task or not task["title"]:
            log.warning(f"Task {i} missing title — skipping")
            continue

        # Truncate title
        task["title"] = str(task["title"])[:MAX_TASK_TITLE_LENGTH]

        # Validate category
        category = task.get("category", "other")
        if category not in VALID_CATEGORIES:
            log.debug(f"Task '{task['title']}' has unknown category '{category}' — defaulting to 'other'")
            task["category"] = "other"

        # Validate times
        start = task.get("start_time", "")
        end = task.get("end_time", "")

        if start and not validate_time_format(start):
            log.warning(f"Task '{task['title']}' has invalid start_time '{start}' — clearing")
            task["start_time"] = None

        if end and not validate_time_format(end):
            log.warning(f"Task '{task['title']}' has invalid end_time '{end}' — clearing")
            task["end_time"] = None

        # Validate priority
        priority = task.get("priority", 1)
        if not isinstance(priority, int) or priority < 1 or priority > 5:
            task["priority"] = 1

        valid_tasks.append(task)

    data["tasks"] = valid_tasks
    data["plan_summary"] = str(data["plan_summary"])[:MAX_PLAN_SUMMARY_LENGTH]

    log.info(f"Plan validation complete: {len(valid_tasks)} valid tasks")
    return data


def validate_memory_content(text: str) -> str:
    """
    Validates and sanitizes memory content.
    Raises ValueError if content is empty or too long.
    """
    if not text or not isinstance(text, str):
        raise ValueError("Memory content cannot be empty")

    text = text.strip()
    if len(text) == 0:
        raise ValueError("Memory content cannot be empty")

    if len(text) > 1000:
        raise ValueError("Memory content exceeds maximum length (1000 chars)")

    return text


def validate_chat_message(text: str) -> str:
    """
    Validates and sanitizes a chat message.
    Raises ValueError if invalid.
    """
    if not text or not isinstance(text, str):
        raise ValueError("Message cannot be empty")

    text = text.strip()
    if len(text) == 0:
        raise ValueError("Message cannot be empty")

    if len(text) > 2000:
        raise ValueError("Message exceeds maximum length (2000 chars)")

    return text


def validate_plan_context(text: str) -> str:
    """Validates and sanitizes the plan generation context string."""
    if not text or not isinstance(text, str):
        return "Plan my day"

    text = text.strip()
    if len(text) > 500:
        text = text[:500]

    return text if text else "Plan my day"
