import json
import re
import logging

logger = logging.getLogger(__name__)

def clean_and_parse_json(text: str):
    """
    Robustly extracts and parses JSON from a string that might contain 
    markdown, chatter, or partial formatting.
    """
    try:
        # 1. Try direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Extract content between first { and last }
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 3. Aggressive cleanup (fix trailing commas, etc if needed - keeping simple for now)
            pass
    
    # 4. If list
    match_list = re.search(r'(\[.*\])', text, re.DOTALL)
    if match_list:
        try:
            return json.loads(match_list.group(1))
        except:
            pass
            
    raise ValueError(f"Could not parse JSON from text: {text[:100]}...")

def validate_and_fix_task_ids(actions: list, context_tasks: list):
    """
    Scans actions for 'reschedule' type. 
    Verifies if 'task_id' exists in 'context_tasks'.
    If not, tries to find a task by title similarity.
    Updates the action in-place with the real ID if found.
    """
    task_map = {t['id']: t for t in context_tasks}
    title_map = {t['title'].lower(): t['id'] for t in context_tasks}

    valid_actions = []
    print(f"DEBUG: Validating {len(actions)} actions against {len(context_tasks)} tasks.")
    print(f"DEBUG: Raw Actions: {actions}")

    for action in actions:
        # 0. Basic Schema Validation
        if not isinstance(action, dict):
            continue
            
        if 'payload' not in action or 'type' not in action:
            print(f"DEBUG: Dropping Malformed Action (Missing payload/type): {action.keys()}")
            continue

        if action.get('type') == 'reschedule':
            payload = action.get('payload', {})
            # Ensure payload is dict
            if not isinstance(payload, dict):
                print(f"DEBUG: Dropping Malformed Payload (Not dict): {payload}")
                continue
                
            tid = payload.get('task_id')
            
            # Case 1: Exact ID Match
            if tid in task_map:
                valid_actions.append(action)
                continue
            
            # Case 2: ID not found, try to find by Label/Title in Action
            # The AI prompt usually puts "Reschedule [Task Name]" in label
            label = action.get('label', '').lower()
            
            # Simple substring search in standard titles
            found_real_id = None
            for t_title, real_id in title_map.items():
                if t_title in label:
                    found_real_id = real_id
                    break
            
            if found_real_id:
                print(f"DEBUG: Auto-Correcting ID {tid} -> {found_real_id} based on title match.")
                action['payload']['task_id'] = found_real_id
                valid_actions.append(action)
            else:
                print(f"DEBUG: Action Dropped. Could not verify Task ID: {tid}")
        else:
            # Pass through non-task actions
            valid_actions.append(action)
            
    return valid_actions
