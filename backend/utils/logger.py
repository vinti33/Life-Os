"""
LifeOS Structured Logging & Infrastructure Utilities
=====================================================
Provides named loggers, timing decorators, and a custom exception hierarchy
for consistent observability across all agents, routers, and services.
"""

import logging
import time
import json
import functools
import traceback
from datetime import datetime


# ---------------------------------------------------------------------------
# Structured Formatter
# ---------------------------------------------------------------------------
class LifeOSFormatter(logging.Formatter):
    """JSON-style structured log formatter for production readability."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "module": record.name,
            "msg": record.getMessage(),
        }
        # Attach extra fields (e.g. duration_ms, user_id)
        for key in ("duration_ms", "user_id", "agent", "action", "error_type"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = traceback.format_exception(*record.exc_info)

        return json.dumps(log_entry, default=str)


# ---------------------------------------------------------------------------
# Logger Factory
# ---------------------------------------------------------------------------
_HANDLER = logging.StreamHandler()
_HANDLER.setFormatter(LifeOSFormatter())


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger with the LifeOS structured formatter attached."""
    logger = logging.getLogger(f"lifeos.{name}")
    if not logger.handlers:
        # Console Handler
        logger.addHandler(_HANDLER)
        
        # File Handler (Added for debugging)
        file_handler = logging.FileHandler("backend.log")
        file_handler.setFormatter(LifeOSFormatter())
        logger.addHandler(file_handler)
        
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger


# ---------------------------------------------------------------------------
# Timing Decorator
# ---------------------------------------------------------------------------
def timed(logger_name: str | None = None):
    """
    Decorator that logs the execution duration of sync and async functions.

    Usage:
        @timed("planner")
        async def generate_plan(...):
            ...
    """

    def decorator(fn):
        _log = get_logger(logger_name or fn.__module__)

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                _log.info(
                    f"{fn.__qualname__} completed",
                    extra={"duration_ms": round(elapsed, 1), "action": fn.__qualname__},
                )
                return result
            except Exception as exc:
                elapsed = (time.perf_counter() - start) * 1000
                _log.error(
                    f"{fn.__qualname__} failed: {exc}",
                    extra={"duration_ms": round(elapsed, 1), "action": fn.__qualname__, "error_type": type(exc).__name__},
                )
                raise

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                _log.info(
                    f"{fn.__qualname__} completed",
                    extra={"duration_ms": round(elapsed, 1), "action": fn.__qualname__},
                )
                return result
            except Exception as exc:
                elapsed = (time.perf_counter() - start) * 1000
                _log.error(
                    f"{fn.__qualname__} failed: {exc}",
                    extra={"duration_ms": round(elapsed, 1), "action": fn.__qualname__, "error_type": type(exc).__name__},
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    return decorator


# ---------------------------------------------------------------------------
# Custom Exception Hierarchy
# ---------------------------------------------------------------------------
class LifeOSError(Exception):
    """Base exception for all LifeOS-specific errors."""

    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message)
        self.context = context or {}


class AgentError(LifeOSError):
    """Raised when an AI agent encounters a non-recoverable failure."""
    pass


class PlannerError(AgentError):
    """Raised specifically by the Planner Agent."""
    pass


class ChatbotError(AgentError):
    """Raised specifically by the Chatbot Agent."""
    pass


class MemoryError(AgentError):
    """Raised specifically by the Memory Agent."""
    pass


class RAGError(LifeOSError):
    """Raised when the RAG pipeline encounters an error."""
    pass


class OrchestratorError(LifeOSError):
    """Raised when the AI Orchestrator pipeline fails."""
    pass


class ExternalServiceError(LifeOSError):
    """Raised when an external dependency (Calendar, LLM, etc.) is unavailable."""
    pass
