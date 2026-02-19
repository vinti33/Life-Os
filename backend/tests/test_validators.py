"""Tests for utils/validators.py — Agent I/O Validation"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils.validators import (
    validate_time_format,
    validate_plan_output,
    validate_memory_content,
    validate_chat_message,
    validate_plan_context,
)


# ---------------------------------------------------------------------------
# validate_time_format
# ---------------------------------------------------------------------------
class TestValidateTimeFormat:
    def test_valid_times(self):
        assert validate_time_format("00:00") is True
        assert validate_time_format("09:30") is True
        assert validate_time_format("12:00") is True
        assert validate_time_format("23:59") is True

    def test_invalid_times(self):
        assert validate_time_format("24:00") is False
        assert validate_time_format("12:60") is False
        assert validate_time_format("9:30") is False  # Missing leading zero
        assert validate_time_format("") is False
        assert validate_time_format("noon") is False
        assert validate_time_format(None) is False

    def test_edge_cases(self):
        assert validate_time_format("  09:30  ") is True  # Validator strips whitespace
        assert validate_time_format("09:30:00") is False   # Seconds not allowed


# ---------------------------------------------------------------------------
# validate_plan_output
# ---------------------------------------------------------------------------
class TestValidatePlanOutput:
    def test_valid_plan(self, sample_plan_output):
        result = validate_plan_output(sample_plan_output)
        assert result["plan_summary"] == "Balanced workday plan"
        assert len(result["tasks"]) == 5

    def test_missing_fields_added(self):
        result = validate_plan_output({})
        assert result["plan_summary"] == "Daily plan"
        assert result["tasks"] == []
        assert result["clarification_questions"] == []

    def test_invalid_category_defaults_to_other(self):
        data = {
            "tasks": [{"title": "Test", "category": "invalid_cat", "start_time": "09:00", "end_time": "10:00"}]
        }
        result = validate_plan_output(data)
        assert result["tasks"][0]["category"] == "other"

    def test_invalid_time_cleared(self):
        data = {
            "tasks": [{"title": "Test", "category": "work", "start_time": "25:00", "end_time": "10:00"}]
        }
        result = validate_plan_output(data)
        assert result["tasks"][0]["start_time"] is None
        assert result["tasks"][0]["end_time"] == "10:00"

    def test_task_without_title_skipped(self):
        data = {"tasks": [{"category": "work"}, {"title": "Valid", "category": "work"}]}
        result = validate_plan_output(data)
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "Valid"

    def test_non_dict_input(self):
        result = validate_plan_output("not a dict")
        assert result["plan_summary"] == "Invalid plan output"
        assert result["tasks"] == []

    def test_priority_clamping(self):
        data = {"tasks": [{"title": "Test", "category": "work", "priority": 99}]}
        result = validate_plan_output(data)
        assert result["tasks"][0]["priority"] == 1

    def test_title_truncation(self):
        data = {"tasks": [{"title": "A" * 300, "category": "work"}]}
        result = validate_plan_output(data)
        assert len(result["tasks"][0]["title"]) == 200


# ---------------------------------------------------------------------------
# validate_memory_content
# ---------------------------------------------------------------------------
class TestValidateMemoryContent:
    def test_valid_content(self):
        assert validate_memory_content("I prefer mornings") == "I prefer mornings"

    def test_strips_whitespace(self):
        assert validate_memory_content("  hello  ") == "hello"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_memory_content("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_memory_content("   ")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="maximum length"):
            validate_memory_content("x" * 1001)

    def test_none_raises(self):
        with pytest.raises(ValueError):
            validate_memory_content(None)


# ---------------------------------------------------------------------------
# validate_chat_message
# ---------------------------------------------------------------------------
class TestValidateChatMessage:
    def test_valid_message(self):
        assert validate_chat_message("Hello!") == "Hello!"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_chat_message("")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="maximum length"):
            validate_chat_message("x" * 2001)


# ---------------------------------------------------------------------------
# validate_plan_context
# ---------------------------------------------------------------------------
class TestValidatePlanContext:
    def test_valid_context(self):
        assert validate_plan_context("Plan my day with exercise") == "Plan my day with exercise"

    def test_empty_defaults(self):
        assert validate_plan_context("") == "Plan my day"
        assert validate_plan_context(None) == "Plan my day"

    def test_truncation(self):
        result = validate_plan_context("x" * 600)
        assert len(result) == 500
