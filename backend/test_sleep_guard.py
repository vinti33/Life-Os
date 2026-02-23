import json
from agents.planner_agent import fix_overlaps, enforce_sleep_lock, time_to_minutes, minutes_to_time

def test_sleep_guard():
    # User's provided data (approximate based on their prompt)
    tasks = [
        {"title": "Morning Planning", "start_time": "07:00", "end_time": "10:00", "category": "work", "priority": 1},
        {"title": "Deep Work Block 1", "start_time": "10:00", "end_time": "13:00", "category": "work", "priority": 1},
        {"title": "Lunch Break", "start_time": "13:00", "end_time": "14:00", "category": "personal", "priority": 3},
        {"title": "Deep Work Block 2", "start_time": "14:00", "end_time": "19:00", "category": "work", "priority": 1},
        {"title": "Short Break", "start_time": "19:00", "end_time": "19:45", "category": "health", "priority": 3},
        {"title": "Afternoon Work", "start_time": "19:45", "end_time": "23:45", "category": "work", "priority": 2},
        {"title": "Team Sync / Review", "start_time": "23:45", "end_time": "23:59", "category": "work", "priority": 2},
        {"title": "Exercise / Walk", "start_time": "23:59", "end_time": "23:59", "category": "health", "priority": 3},
        {"title": "Dinner", "start_time": "23:59", "end_time": "23:59", "category": "personal", "priority": 3},
        {"title": "Personal Time / Reading", "start_time": "23:59", "end_time": "23:59", "category": "personal", "priority": 4},
        {"title": "Wind Down & Sleep Prep", "start_time": "23:59", "end_time": "23:59", "category": "health", "priority": 5},
    ]

    profile = {"sleep_time": "22:45"}
    sleep_limit = time_to_minutes(profile["sleep_time"])

    print(f"--- Initial Tasks: {len(tasks)} ---")
    for t in tasks:
        print(f"{t['start_time']}-{t['end_time']}: {t['title']}")

    # 1. Enforce Sleep Lock
    locked_tasks = enforce_sleep_lock(tasks, profile)
    print(f"\n--- After enforce_sleep_lock: {len(locked_tasks)} tasks ---")
    for t in locked_tasks:
        print(f"{t['start_time']}-{t['end_time']}: {t['title']}")

    # 2. Fix Overlaps with Sleep Boundary
    final_tasks = fix_overlaps(locked_tasks, max_minutes=sleep_limit)
    print(f"\n--- After fix_overlaps: {len(final_tasks)} tasks ---")
    for t in final_tasks:
        print(f"{t['start_time']}-{t['end_time']}: {t['title']}")

    # Assertions
    for t in final_tasks:
        end = time_to_minutes(t["end_time"])
        assert end <= sleep_limit, f"Task {t['title']} ends at {t['end_time']} which is past {profile['sleep_time']}"

    print("\nVERIFICATION PASSED: All tasks respect the 22:45 sleep boundary.")

if __name__ == "__main__":
    test_sleep_guard()
