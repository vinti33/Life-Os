"""
LifeOS Application — Production-Hardened Entry Point
=====================================================
FastAPI application with rate limiting, CORS lockdown,
structured error handling, and health diagnostics.
"""

import time
import uuid
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.middleware.base import BaseHTTPMiddleware
from database import init_db
from config import settings
from utils.logger import get_logger
from utils.cache import get_cache
from utils.queue import get_queue

log = get_logger("app")

app = FastAPI(
    title="LifeOS AI API",
    version=settings.VERSION,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)


# ---------------------------------------------------------------------------
# Middleware: Request ID + Timing
# ---------------------------------------------------------------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds request ID and timing to every request."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round(elapsed))

        log.info(
            f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.0f}ms) "
            f"[rid={request_id}]"
        )
        return response


# ---------------------------------------------------------------------------
# Middleware: Rate Limiting (in-memory, per-IP)
# ---------------------------------------------------------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter — per IP, per minute window."""

    def __init__(self, app, max_requests: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip health and docs endpoints
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60.0  # 1 minute

        # Clean old entries
        self._buckets[client_ip] = [
            t for t in self._buckets[client_ip] if now - t < window
        ]

        if len(self._buckets[client_ip]) >= self.max_requests:
            log.warning(f"Rate limit exceeded: ip={client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
            )

        self._buckets[client_ip].append(now)
        return await call_next(request)


# Register middleware (order matters: first registered = outermost)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=settings.RATE_LIMIT_PER_MIN)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled exception: {exc}", exc_info=True)
    # In production, hide internal details
    detail = "An internal error occurred." if settings.is_production else str(exc)
    headers = {
        "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(
        status_code=500,
        headers=headers,
        content={"status": "error", "message": detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    await init_db()
    
    # Initialize Redis & Queue
    await get_cache().connect()
    await get_queue().connect()

    log.info(
        f"LifeOS {settings.VERSION} started | env={settings.ENVIRONMENT} | "
        f"model={settings.AI_MODEL} | cors={settings.cors_origins_list}"
    )


@app.on_event("shutdown")
async def on_shutdown():
    await get_queue().shutdown()
    log.info("LifeOS shutdown complete")


# ---------------------------------------------------------------------------
# Health & Diagnostics
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Component-level health diagnostics."""
    diagnostics = {
        "status": "ok",
        "service": "LifeOS",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }

    # Check RAG health
    try:
        from rag.manager import get_rag_manager
        rag = get_rag_manager()
        diagnostics["rag"] = rag.health_check()
    except Exception as e:
        diagnostics["rag"] = {"status": "error", "detail": str(e)}

    # Check DB connectivity
    try:
        from models import User
        count = await User.count()
        diagnostics["database"] = {"status": "ok", "users": count}
    except Exception as e:
        diagnostics["database"] = {"status": "error", "detail": str(e)}

    return diagnostics


# ---------------------------------------------------------------------------
# Router Registration
# ---------------------------------------------------------------------------
from routers import auth, profile, plan, task, stats, chat, upgrade, external, google_auth, finance, progress

api_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(profile.router, prefix=api_prefix)
app.include_router(plan.router, prefix=api_prefix)
app.include_router(task.router, prefix=api_prefix)
app.include_router(stats.router, prefix=api_prefix)
app.include_router(chat.router, prefix=api_prefix)
app.include_router(upgrade.router, prefix=api_prefix)
app.include_router(external.router, prefix=api_prefix)
app.include_router(google_auth.router, prefix=api_prefix)
app.include_router(finance.router, prefix=api_prefix)
app.include_router(progress.router, prefix=api_prefix)

from routers import actions
app.include_router(actions.router, prefix=api_prefix)

from routers import history, memory, metrics
app.include_router(history.router, prefix=api_prefix)
app.include_router(memory.router, prefix=api_prefix)
app.include_router(metrics.router, prefix=api_prefix)
