# LifeOS System Architecture

## 1. System Overview

LifeOS is a full-stack personal optimization platform designed to run locally with privacy-first AI.

### High-Level Components
- **Frontend**: Next.js (React) application serving the user interface.
- **Backend**: FastAPI (Python) application handling business logic, database interactions, and AI orchestration.
- **Database**: MongoDB (via Beanie ODM) for all structured data (Users, Plans, Tasks, Memories).
- **AI/LLM**: Local Ollama instance (running phi3:mini/Mistral/Llama) or OpenAI-compatible API.
- **Vector Store**: FAISS + Nomic Embeddings for RAG (Retrieval-Augmented Generation).

---

## 2. Directory Structure & Key Files

### Backend (`/backend`)

| Path | Description |
|------|-------------|
| `main.py` | **Entry Point**. Initializes FastAPI, CORS, routers, and global exception handlers. |
| `ai_orchestrator.py` | **Central Pipeline**. 3-stage orchestrator (Assemble → Generate → Persist) with fallback chains. |
| `routers/` | **API Endpoints**. Separated by domain (chat, plan, task, stats, auth, etc.). |
| `agents/` | **AI Workers**. Specialized agent classes for planning, chat, memory, review, tracking, calendar. |
| `models.py` | **Database Schema**. Beanie Document definitions (User, Task, Plan, Pattern, UserMemory, etc.). |
| `rag/` | **Memory System**. FAISS-based vector search with relevance scoring and health monitoring. |
| `utils/logger.py` | **Logging Framework**. Structured JSON logging, `@timed` decorator, custom exception hierarchy. |

### Frontend (`/frontend`)

| Path | Description |
|------|-------------|
| `src/pages/` | **Routes**. `chat.jsx` (Chat UI), `dashboard.jsx` (Main View). |
| `src/components/` | **UI Components**. Reusable bits like `ChatBubble`, `Button`. |
| `src/services/` | **API Client**. Functions to call backend (e.g., `taskService.js`). |
| `src/store/` | **State Management**. Zustand stores (e.g., `chatStore.js`). |

---

## 3. Logging Framework

All backend components use the structured logging system from `utils/logger.py`.

### Components
- **`LifeOSFormatter`**: JSON-formatted log output with timestamps, module names, and optional fields (duration_ms, user_id, agent, error_type).
- **`get_logger(name)`**: Factory function returning a named logger (e.g., `lifeos.orchestrator`).
- **`@timed(name)`**: Decorator that logs execution duration for sync and async functions.

### Exception Hierarchy
```
LifeOSError
├── AgentError
│   ├── PlannerError
│   ├── ChatbotError
│   └── MemoryError
├── RAGError
├── OrchestratorError
└── ExternalServiceError
```

---

## 4. Agent Pipeline (AI Orchestrator)

The `AIOrchestrator` implements a 3-stage pipeline with fallback handling:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  ASSEMBLE   │ →  │  GENERATE   │ →  │   PERSIST   │
│ Profile     │    │ PlannerAgent│    │ Plan + Tasks│
│ Stats       │    │ (+ fallback)│    │ batch insert│
│ Patterns    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Fallback Chain
If the PlannerAgent fails (LLM timeout, parse error, zero tasks), the orchestrator generates a **safe fallback plan** based on the user's profile (wake/sleep/work times).

### Agent Registry
Agents are registered in `_AGENT_REGISTRY` for dynamic resolution and future extensibility.

---

## 5. RAG System

### Retrieval Strategy
- **Multi-result**: Returns top-k (default k=3) results with deduplication.
- **Relevance Scoring**: `score = 1.0 / (1.0 + L2_distance)` — normalized 0–1.
- **Conditional Bypass**: Generic requests ("Plan my day") skip RAG to save embedding + search time.

### Health Monitoring
`health_check()` returns: index_loaded, indexed_entries, source_entries, index_stale, embedding_dim.

### Auto-Rebuild
If `data.json` has more entries than the loaded index, the index is automatically rebuilt on next load.

---

## 6. Memory Lifecycle

### Tiers
- **SHORT_TERM**: Default tier. Confidence decays daily if not accessed.
- **LONG_TERM**: Promoted from short-term when confidence ≥ 0.8 and access_count ≥ 3.

### Lifecycle Operations
| Operation | Trigger | Effect |
|-----------|---------|--------|
| **Decay** | Daily cron | Confidence -= 0.1/day for idle short-term memories |
| **Prune** | Daily cron | Delete short-term memories below 0.3 confidence |
| **Promote** | Daily cron | Move high-confidence, frequently-accessed memories to LONG_TERM |
| **Reinforce** | Duplicate fact detected | Boost confidence to 1.0, increment access count |

### Prioritized Retrieval
`get_prioritized_context()` returns memories sorted by `confidence × recency_weight`.

---

## 7. How the Chatbot Works

1.  **User Input**: User types a message in `chat.jsx`.
2.  **API Call**: Frontend sends POST to `/chat/message`.
3.  **Context Assembly** (`ai_orchestrator.py`): Pulls profile, stats, patterns, current plan.
4.  **RAG Injection** (`rag/manager.py`): Retrieves relevant knowledge (scored, k=3).
5.  **Agent Processing** (`agents/chatbot_agent.py`): Deterministic intent detection → structured JSON response with actions.
6.  **Memory Extraction**: Background task extracts permanent facts from user messages.
7.  **Response**: JSON with `reply`, `actions` (add_task, reschedule), `clarification_questions`.

---

## 8. Error Handling

- **Planner Agent**: Retry with exponential backoff (max 2 attempts), JSON recovery from mixed text.
- **Chat Router**: Error boundary around agent calls — returns graceful error message instead of 500.
- **Plan Router**: Try/except with structured HTTP error responses and request timing.
- **Calendar Sync**: Non-blocking failure — plan approval succeeds even if calendar sync fails.
- **Memory Agent**: Runs as BackgroundTask — failures don't block the chat response.

---

## 9. Data Flow for "Rescheduling"

1.  **Detection**: User says "Move gym to 6pm".
2.  **Analysis**: `chatbot_agent.py` recognizes `reschedule` intent.
3.  **Action Generation**: Agent outputs JSON action with `task_id`, `start_time`, `end_time`.
4.  **UI Rendering**: `ChatBubble.jsx` renders a "Reschedule Task" button.
5.  **Execution**: User clicks → `taskService.reschedule(...)` → CalendarAgent handles conflicts.
