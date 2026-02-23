"""
LifeOS Chatbot Agent — Deterministic Intent-Based Response System
==================================================================
Handles add_task, reschedule, and fallback intents without LLM dependency.
Uses regex-based time extraction and rule-based task matching.
"""

from typing import List, Dict, Any
import re
import uuid
from utils.logger import get_logger

log = get_logger("chatbot_agent")

# Intent keywords
_RESCHEDULE_KEYWORDS = frozenset(["move", "shift", "reschedule", "change"])
_ADD_KEYWORDS = frozenset(["add", "create", "schedule", "new"])
_DELETE_KEYWORDS = frozenset(["remove", "delete", "cancel", "drop"])
_EDIT_PLAN_KEYWORDS = frozenset([
    "break", "split", "expand", "restructure", "reorganize", "organize",
    "make smaller", "more detailed", "break down", "rearrange", "simplify",
    "morning routine", "evening routine", "workout session", "adjust plan",
    "update plan", "modify plan", "plan my", "morning", "afternoon", "evening",
    "lunch to morning", "breakfast to morning", "dinner to evening"
])


class ChatbotAgent:
    """
    Safe, deterministic agent for task management.
    Compatible with existing routers/chat.py interface.
    """

    def __init__(self, context: Dict[str, Any], rag_manager: Any = None):
        self.context = context
        self.rag_manager = rag_manager

    async def send_message(self, user_id: int, message: str) -> Dict[str, Any]:
        """Bridge method matching the interface expected by routers/chat.py."""
        current_plan = self.context.get("current_plan", [])
        log.info(f"Processing message for user={user_id}, tasks_in_context={len(current_plan)}")
        return await self.run(message, current_plan)

    # -------------------------
    # Public Entry Point
    # -------------------------
    async def run(self, message: str, tasks: List[Dict]) -> Dict:
        intent = self._detect_intent(message)
        log.info(f"Detected intent: {intent} for message: '{message[:40]}...'")

        if intent == "add_task":
            return self._handle_add_task(message)
        if intent == "reschedule":
            return self._handle_reschedule(message, tasks)
        if intent == "delete_task":
            return self._handle_delete_task(message, tasks)
        if intent == "edit_plan":
            return self._handle_edit_plan(message)
        return await self._fallback(message)

    # -------------------------
    # Intent Detection
    # -------------------------
    def _detect_intent(self, msg: str) -> str:
        msg_lower = msg.lower()
        if any(w in msg_lower for w in _DELETE_KEYWORDS):
            return "delete_task"
        if any(w in msg_lower for w in _RESCHEDULE_KEYWORDS):
            return "reschedule"
        if any(w in msg_lower for w in _ADD_KEYWORDS):
            return "add_task"
        if any(w in msg_lower for w in _EDIT_PLAN_KEYWORDS):
            return "edit_plan"
        return "unknown"

    # -------------------------
    # Time Extraction
    # -------------------------
    def _extract_times(self, text: str) -> List[str]:
        """Extracts validated HH:MM time patterns (colon, am/pm, or preposition-led)."""
        valid_times = []
        text_lower = text.lower()
        
        # Combined Regex for strict time extraction
        # 1. Colon Time: 10:00, 10:00pm
        # 2. AMPM Time: 5pm, 5 am
        # 3. Preposition Time: at 5, to 5 (requires preposition to avoid 'Session 1')
        pat = r'\b(\d{1,2}:\d{2}(?:\s*[ap]m)?)\b|\b(\d{1,2}\s*[ap]m)\b|\b(?:at|to|from|until|by)\s+(\d{1,2}(?::\d{2})?)\b'
        
        for m in re.finditer(pat, text_lower):
            # Get the matched group (only one will be non-None)
            t = next((x for x in m.groups() if x is not None), None)
            if not t: continue
            
            # Normalize to HH:MM
            clean_t = t.replace(" ", "")
            is_pm = "pm" in clean_t
            is_am = "am" in clean_t
            clean_t = clean_t.replace("am", "").replace("pm", "")
            
            try:
                if ":" in clean_t:
                    h, minute = map(int, clean_t.split(":"))
                else:
                    h = int(clean_t)
                    minute = 0
                
                if is_pm and h < 12: h += 12
                if is_am and h == 12: h = 0
                
                if 0 <= h <= 23 and 0 <= minute <= 59:
                    valid_times.append(f"{h:02d}:{minute:02d}")
            except ValueError:
                continue

        log.debug(f"Extracted times: {valid_times} from '{text[:40]}...'")
        return valid_times

    def _find_matching_tasks(self, message: str, tasks: List[Dict]) -> List[Dict]:
        return [t for t in tasks if t["title"].lower() in message.lower()]

    # -------------------------
    # Add Task Handler
    # -------------------------
    def _extract_title(self, message: str) -> str:
        """Extract a clean task title by stripping command words and time phrases."""
        title = message.lower()
        # Remove command words
        for word in ["add", "create", "schedule", "new", "task"]:
            title = title.replace(word, "")
        # Remove time phrases like "at 8am", "from 8am", "to 9pm", "8:00", "9am"
        title = re.sub(r'\b(at|from|to|between)\b', '', title)
        title = re.sub(r'\b\d{1,2}(:\d{2})?\s*(am|pm)?\b', '', title)
        # Clean up extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        return title.title() if title else "New Task"

    def _handle_add_task(self, message: str) -> Dict:
        times = self._extract_times(message)
        if not times:
            return {
                "reply": "I need a time to add this task.",
                "actions": [],
                "clarification_questions": ["What time should this task start?"],
            }

        start = times[0]
        end = times[1] if len(times) >= 2 else f"{min(int(start[:2]) + 1, 23):02d}:{start[3:]}"

        title = self._extract_title(message)

        log.info(f"Add task: '{title}' from {start} to {end}")
        return {
            "type": "ACTION_RESPONSE",
            "message": f"I can add '{title}' from {start} to {end}. Confirm?",
            "action": {
                "type": "ADD_TASK",
                "label": "Add Task",
                "payload": {
                    "title": title,
                    "start_time": start,
                    "end_time": end,
                    "category": "general"
                },
            }
        }

    # -------------------------
    # Edit Plan Handler
    # -------------------------
    def _handle_edit_plan(self, message: str) -> Dict:
        """Handles requests to modify/restructure/expand parts of the existing plan."""
        log.info(f"Edit plan intent detected for: '{message[:60]}'")
        return {
            "type": "ACTION_RESPONSE",
            "message": f"I'll update your plan based on: '{message}'. Confirm?",
            "action": {
                "type": "EDIT_PLAN",
                "label": "Update Plan",
                "payload": {
                    "context": message,
                    "plan_type": "daily",
                },
            },
        }

    # -------------------------
    # Delete Task Handler
    # -------------------------
    def _handle_delete_task(self, message: str, tasks: List[Dict]) -> Dict:
        matches = self._find_matching_tasks(message, tasks)

        if not matches:
            # Try a looser match — strip delete keywords and search
            stripped = message.lower()
            for word in ["remove", "delete", "cancel", "drop"]:
                stripped = stripped.replace(word, "")
            stripped = stripped.strip()
            matches = [t for t in tasks if stripped and stripped in t["title"].lower()]

        if not matches:
            return {
                "type": "ACTION_RESPONSE",
                "message": "I couldn't find that task in your plan. Which task do you want to remove?",
                "action": None,
            }

        if len(matches) > 1:
            names = ", ".join(f"'{t['title']}'" for t in matches)
            return {
                "type": "ACTION_RESPONSE",
                "message": f"Multiple tasks match. Did you mean: {names}?",
                "action": None,
            }

        task = matches[0]
        task_id = task.get("id") or task.get("_id")
        if not task_id:
            log.warning(f"Delete match found but no ID: {task}")
            return {
                "type": "ACTION_RESPONSE",
                "message": "I found the task but couldn't get its ID. Try refreshing.",
                "action": None,
            }

        log.info(f"Delete task: '{task['title']}' id={task_id}")
        return {
            "type": "ACTION_RESPONSE",
            "message": f"Remove '{task['title']}'? This cannot be undone.",
            "action": {
                "type": "DELETE_TASK",
                "label": "Remove Task",
                "payload": {
                    "task_id": str(task_id),
                    "title": task["title"],
                },
            },
        }

    # -------------------------
    # Reschedule Handler
    # -------------------------
    def _handle_reschedule(self, message: str, tasks: List[Dict]) -> Dict:
        matches = self._find_matching_tasks(message, tasks)

        if not matches:
            return {
                "reply": "I couldn't find that task.",
                "actions": [],
                "clarification_questions": ["Which task do you want to move?"],
            }

        if len(matches) > 1:
            return {
                "reply": "Multiple tasks match your request.",
                "actions": [],
                "clarification_questions": [
                    f"Did you mean: {', '.join(t['title'] for t in matches)}?"
                ],
            }

        times = self._extract_times(message)
        if not times:
            return {
                "reply": "I need a new time.",
                "actions": [],
                "clarification_questions": ["What time should I move it to?"],
            }

        task = matches[0]
        new_start = times[0]
        new_end = times[1] if len(times) >= 2 else f"{min(int(new_start[:2]) + 1, 23):02d}:{new_start[3:]}"

        # Ensure we have a task ID
        task_id = task.get("id") or task.get("_id")
        if not task_id:
             log.warning(f"Task match found but no ID: {task}")
             return { "reply": "I found the task but lost its ID. Please try refreshing.", "actions": [] }

        log.info(f"Reschedule: '{task['title']}' → {new_start}-{new_end}")
        return {
            "type": "ACTION_RESPONSE",
            "message": f"I can move '{task['title']}' to {new_start}. Confirm?",
            "action": {
                "type": "UPDATE_TASK",
                "label": "Reschedule",
                "payload": {
                    "task_id": str(task_id),
                    "start_time": new_start,
                    "end_time": new_end
                },
            }
        }

    # -------------------------
    # Fallback with LLM
    # -------------------------
    async def _fallback(self, message: str) -> Dict:
        """Attempts to understand intent via LLM if regex fails."""
        log.info("Regex failed — attempting LLM fallback")
        return await self._handle_llm_fallback(message)

    async def _handle_llm_fallback(self, message: str) -> Dict:
        import json
        import requests
        from config import settings

        system_prompt = f"""You are the LifeOS Chat Assistant.
The user's request matched no regex rules. Simplify their request into a structured action.
CURRENT CONTEXT: {len(self.context.get("current_plan", []))} tasks in plan.

SUPPORTED ACTIONS:
- ADD_TASK: Create a new task at a specific time.
- UPDATE_TASK: Move or change a task's time.
- DELETE_TASK: Remove a task by name.
- EDIT_PLAN: Modify the existing plan (add tasks, remove tasks, restructure, break down tasks, etc.).
- GENERATE_ROUTINE: Create a brand new plan from scratch (only use when user explicitly says "create new plan" or "start over").
- REPLY: Just a conversational text answer (no plan changes).

  "action": {{
    "type": "ADD_TASK", 
    "label": "Button Text",
    "payload": {{ "title": "Buy Milk", "start_time": "18:00", "end_time": "18:30", "category": "chore" }}
  }}
}}

IMPORTANT RULES:
1. NO OVERLAPS: Ensure the suggested times do not overlap with existing tasks or each other.
2. MEAL TIMES: Respect realistic meal windows (Breakfast ~08:00, Lunch ~13:00, Dinner ~20:00) unless explicitly asked to change (e.g., "lunch to morning").
3. MORNING REQUIREMENTS: If a user specifies a morning requirement, ensure it is placed within the 06:00-11:00 window.
4. If the action is just to reply with text, SET "action": null. DO NOT create a REPLY action object.
5. If the user asks to "break down", "create routine", or "plan", use GENERATE_ROUTINE.

EXAMPLES:
User: "Add gym at 6pm"
Output:
{{
  "type": "ACTION_RESPONSE",
  "message": "I can add Gym for 6pm. Confirm?",
  "action": {{ "type": "ADD_TASK", "label": "Add Gym", "payload": {{ "title": "Gym", "start_time": "18:00", "end_time": "19:00", "category": "health" }} }}
}}

User: "Why is the sky blue?"
Output:
{{
  "type": "ACTION_RESPONSE",
  "message": "The sky is blue because of Rayleigh scattering of sunlight.",
  "action": null
}}

User: "Break morning routine into small tasks"
Output:
{{
  "type": "ACTION_RESPONSE",
  "message": "I'll break your morning routine into smaller steps.",
  "action": {{ "type": "EDIT_PLAN", "label": "Update Plan", "payload": {{ "context": "Break morning routine into small tasks", "plan_type": "daily" }} }}
}}

User: "Add a workout after work"
Output:
{{
  "type": "ACTION_RESPONSE",
  "message": "I'll add a workout block after your work hours.",
  "action": {{ "type": "EDIT_PLAN", "label": "Update Plan", "payload": {{ "context": "Add a workout after work", "plan_type": "daily" }} }}
}}

User: "Remove my lunch break"
Output:
{{
  "type": "ACTION_RESPONSE",
  "message": "I'll remove the lunch break from your plan.",
  "action": {{ "type": "EDIT_PLAN", "label": "Update Plan", "payload": {{ "context": "Remove lunch break", "plan_type": "daily" }} }}
}}

Refuse to output anything else. JSON ONLY.
        """

        # Retry logic with host fallback
        # 1. Start with configured URL
        hosts_to_try = [settings.OPENAI_BASE_URL.rstrip("/")]
        
        # 2. Add standard Docker gateways (Linux/Mac/Windows variations)
        # 172.17.0.1 is standard bridge. 172.18-19.0.1 are common for compose networks.
        fallback_ips = [
            "http://172.17.0.1:11434/v1",
            "http://172.18.0.1:11434/v1",
            "http://172.19.0.1:11434/v1",
            "http://172.20.0.1:11434/v1",
            "http://host.docker.internal:11434/v1",
            "http://127.0.0.1:11434/v1",
            "http://localhost:11434/v1"
        ]
        
        # 3. Dynamic Gateway Discovery (The "Silver Bullet" for Linux Docker)
        try:
            with open("/proc/net/route") as fh:
                for line in fh:
                    fields = line.strip().split()
                    # Destination 00000000 means default gateway
                    if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                        continue
                    
                    # Parse hex IP
                    import socket
                    import struct
                    gateway_ip = socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
                    log.info(f"Discovered dynamic gateway IP: {gateway_ip}")
                    fallback_ips.insert(0, f"http://{gateway_ip}:11434/v1")
                    break
        except Exception as e:
            log.warning(f"Failed to discover default gateway: {e}")

        hosts_to_try.extend(fallback_ips)

        # Deduplicate while preserving order
        hosts_to_try = list(dict.fromkeys(hosts_to_try))
        log.info(f"LLM Fallback: Candidate hosts: {hosts_to_try}")

        # Helper to check connectivity fast
        def _is_host_reachable(base_url: str) -> bool:
            try:
                # Try a lightweight endpoint or just the root with very short timeout
                # We expect ANY response (200, 404, 401), just not a timeout/connection error
                requests.get(f"{base_url}/models", timeout=(2, 2))
                return True
            except Exception:
                return False

        # Filter for reachable hosts first
        reachable_hosts = []
        for host in hosts_to_try:
             # Run checking in thread to avoid blocking loop
             if await asyncio.to_thread(_is_host_reachable, host):
                  reachable_hosts.append(host)
                  log.info(f"Host {host} is reachable!")
                  break # Found one, good enough? Should we stop at first working one? YES.
             else:
                  log.debug(f"Host {host} unreachable.")
        
        if not reachable_hosts:
             log.warning("No reachable LLM hosts found.")
             # Fallback to localhost just in case the check was too strict? 
             # Or just fail.
             reachable_hosts = ["http://127.0.0.1:11434/v1"] # Desperation move

        for base_url in reachable_hosts:
            try:
                log.info(f"Attempting generation on: {base_url}")
                def _call():
                    # timeout=(connect, read) -> fail fast on bad IP
                    url = f"{base_url}/chat/completions"
                    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
                    data = {
                        "model": settings.AI_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.3
                    }
                    return requests.post(url, json=data, headers=headers, timeout=(5, 300)).json()

                resp = await asyncio.to_thread(_call)
                
                # Check for API errors (like OOM)
                if "error" in resp:
                    error_msg = resp["error"].get("message", "")
                    log.error(f"LLM API Error on {base_url}: {error_msg}")
                    if "memory" in error_msg.lower():
                        return {
                            "reply": "I'm running out of memory! Please close some other applications so I can think clearly.",
                            "actions": [],
                            "clarification_questions": []
                        }
                    continue

                if "choices" not in resp:
                    log.error(f"LLM Response missing choices: {resp}")
                    continue
                    
                content = resp["choices"][0]["message"]["content"]
                result = json.loads(content)
                # Normalize action type to uppercase to prevent case mismatch bugs
                if result.get("action") and result["action"].get("type"):
                    result["action"]["type"] = result["action"]["type"].upper()
                return result
            
            except Exception as e:
                log.error(f"LLM Fallback failed on {base_url}: {e.__class__.__name__}: {e}")
                continue

        # If all hosts fail
        log.error("All LLM fallback attempts failed.")
        return {
            "type": "ACTION_RESPONSE",
            "message": "I'm having trouble processing that request right now. Please try rephrasing, e.g. 'Add gym at 6pm' or 'Break morning routine into tasks'.",
            "action": None,
        }

import asyncio
