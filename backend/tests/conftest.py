"""
LifeOS Test Fixtures — Shared test infrastructure
===================================================
Provides async test fixtures, mock factories, and
reusable test data for all test modules.
"""

import pytest
import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_profile():
    """Returns a realistic user profile dict."""
    return {
        "work_hours": "09:00 - 18:00",
        "work_start_time": "09:00",
        "work_end_time": "18:00",
        "sleep_wake": "23:00 - 06:30",
        "wake_time": "06:30",
        "sleep_time": "23:00",
        "health_goals": "Exercise daily",
        "learning_goals": "Learn Python",
        "finance_goals": "Save $5000",
        "role": "Working",
        "constraints": "No meetings before 10am",
    }


@pytest.fixture
def sample_plan_output():
    """Returns a valid plan output from the planner agent."""
    return {
        "plan_summary": "Balanced workday plan",
        "tasks": [
            {
                "title": "Morning Routine",
                "category": "health",
                "start_time": "06:30",
                "end_time": "07:30",
                "priority": 2,
            },
            {
                "title": "Deep Work Session",
                "category": "work",
                "start_time": "09:00",
                "end_time": "12:00",
                "priority": 1,
            },
            {
                "title": "Lunch Break",
                "category": "personal",
                "start_time": "12:00",
                "end_time": "13:00",
                "priority": 3,
            },
            {
                "title": "Afternoon Work",
                "category": "work",
                "start_time": "13:00",
                "end_time": "18:00",
                "priority": 1,
            },
            {
                "title": "Evening Exercise",
                "category": "health",
                "start_time": "18:30",
                "end_time": "19:30",
                "priority": 2,
            },
        ],
        "clarification_questions": [],
    }


@pytest.fixture
def sample_tasks():
    """Returns a list of task dicts for chatbot testing."""
    return [
        {"id": "task_001", "title": "Morning Run", "status": "pending", "start_time": "06:30", "end_time": "07:30"},
        {"id": "task_002", "title": "Deep Work", "status": "pending", "start_time": "09:00", "end_time": "12:00"},
        {"id": "task_003", "title": "Lunch Break", "status": "pending", "start_time": "12:00", "end_time": "13:00"},
    ]
