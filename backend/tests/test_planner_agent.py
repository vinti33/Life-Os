"""Tests for agents/planner_agent.py — Enforcement & JSON Recovery"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from agents.planner_agent import enforce_work_school_lock, _recover_json


class TestEnforceWorkSchoolLock:
    def setup_method(self):
        self.working_profile = {
            "role": "Working",
            "work_start_time": "09:00",
            "work_end_time": "18:00",
        }
        self.student_profile = {
            "role": "Student",
            "work_start_time": "08:00",
            "work_end_time": "15:00",
        }
        self.free_profile = {"role": "House Free"}

    def test_work_tasks_allowed_in_work_zone(self):
        tasks = [{"title": "Coding", "category": "work", "start_time": "10:00", "end_time": "12:00"}]
        result = enforce_work_school_lock(tasks, self.working_profile)
        assert len(result) == 1

    def test_personal_tasks_stripped_from_work_zone(self):
        tasks = [{"title": "Yoga", "category": "health", "start_time": "10:00", "end_time": "11:00"}]
        result = enforce_work_school_lock(tasks, self.working_profile)
        assert len(result) == 0

    def test_lunch_allowed_in_work_zone(self):
        tasks = [{
            "title": "Lunch Break",
            "category": "personal",
            "start_time": "12:00",
            "end_time": "13:00",
        }]
        result = enforce_work_school_lock(tasks, self.working_profile)
        assert len(result) == 1

    def test_tasks_outside_work_zone_kept(self):
        tasks = [
            {"title": "Morning Run", "category": "health", "start_time": "06:30", "end_time": "07:30"},
            {"title": "Evening Read", "category": "personal", "start_time": "19:00", "end_time": "20:00"},
        ]
        result = enforce_work_school_lock(tasks, self.working_profile)
        assert len(result) == 2

    def test_free_profile_keeps_all(self):
        tasks = [
            {"title": "Yoga", "category": "health", "start_time": "10:00", "end_time": "11:00"},
            {"title": "Gaming", "category": "personal", "start_time": "14:00", "end_time": "16:00"},
        ]
        result = enforce_work_school_lock(tasks, self.free_profile)
        assert len(result) == 2

    def test_student_profile_enforced(self):
        tasks = [{"title": "Gaming", "category": "personal", "start_time": "10:00", "end_time": "11:00"}]
        result = enforce_work_school_lock(tasks, self.student_profile)
        assert len(result) == 0

    def test_invalid_time_in_task_kept(self):
        tasks = [{"title": "Bad Task", "category": "work", "start_time": "bad", "end_time": "worse"}]
        result = enforce_work_school_lock(tasks, self.working_profile)
        assert len(result) == 1  # Kept because of error handling

    def test_learning_allowed_in_work_zone(self):
        tasks = [{"title": "Course", "category": "learning", "start_time": "10:00", "end_time": "12:00"}]
        result = enforce_work_school_lock(tasks, self.working_profile)
        assert len(result) == 1


class TestRecoverJson:
    def test_clean_json(self):
        result = _recover_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_in_mixed_text(self):
        text = 'Here is the plan:\n{"plan_summary": "test", "tasks": []}\nEnd of response.'
        result = _recover_json(text)
        assert result["plan_summary"] == "test"

    def test_no_json_returns_none(self):
        result = _recover_json("Just plain text with no JSON at all")
        assert result is None

    def test_invalid_json_returns_none(self):
        result = _recover_json("{broken json without closing")
        assert result is None
