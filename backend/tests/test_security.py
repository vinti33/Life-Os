"""Tests for utils/security.py — Security Primitives"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils.security import sanitize_string, validate_time_string, validate_object_id


class TestSanitizeString:
    def test_basic_input(self):
        assert sanitize_string("hello world") == "hello world"

    def test_strips_whitespace(self):
        assert sanitize_string("  hello  ") == "hello"

    def test_escapes_html(self):
        result = sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_removes_null_bytes(self):
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result
        assert result == "helloworld"

    def test_truncation(self):
        result = sanitize_string("a" * 200, max_length=100)
        assert len(result) == 100

    def test_empty_string(self):
        assert sanitize_string("") == ""

    def test_none_returns_empty(self):
        assert sanitize_string(None) == ""


class TestValidateTimeString:
    def test_valid(self):
        assert validate_time_string("09:30") is True
        assert validate_time_string("00:00") is True
        assert validate_time_string("23:59") is True

    def test_invalid(self):
        assert validate_time_string("24:00") is False
        assert validate_time_string("12:60") is False
        assert validate_time_string("9:30") is False
        assert validate_time_string("") is False
        assert validate_time_string(None) is False


class TestValidateObjectId:
    def test_invalid_raises_http_400(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_object_id("not-a-valid-id")
        assert exc_info.value.status_code == 400

    def test_valid_id(self):
        # A valid 24-char hex string
        result = validate_object_id("507f1f77bcf86cd799439011")
        assert str(result) == "507f1f77bcf86cd799439011"
