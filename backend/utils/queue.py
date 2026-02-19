"""
LifeOS Task Queue — Redis-based Background Worker
===================================================
A lightweight async job queue using Redis lists.
Supports job enqueuing and a worker process for background execution.
"""

import asyncio
import json
import logging
from typing import Callable, Any, Dict
from redis.asyncio import Redis, from_url
from config import settings

log = logging.getLogger("queue")

JOB_QUEUE_KEY = "lifeos:jobs"


class TaskQueue:
    _instance = None

    def __init__(self):
        self.client: Redis | None = None
        self.handlers: Dict[str, Callable] = {}
        self.is_running = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TaskQueue()
        return cls._instance

    async def connect(self):
        """Connects to Redis."""
        if self.client:
            return
        try:
            self.client = from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await self.client.ping()
            self.is_running = True
            log.info("TaskQueue connected to Redis")
            # Start consumer loop in background
            asyncio.create_task(self._worker_loop())
        except Exception as e:
            log.error(f"TaskQueue connection failed: {e}")
            self.is_running = False

    def register_handler(self, job_name: str, handler: Callable):
        """Registers an async function to handle a job type."""
        self.handlers[job_name] = handler
        log.info(f"Registered job handler: {job_name}")

    async def enqueue(self, job_name: str, payload: Any):
        """Push a job to the Redis queue."""
        if not self.client or not self.is_running:
            log.warning(f"Queue not ready, dropping job: {job_name}")
            return

        job_data = json.dumps({"name": job_name, "payload": payload})
        await self.client.rpush(JOB_QUEUE_KEY, job_data)
        log.debug(f"Enqueued job: {job_name}")

    async def _worker_loop(self):
        """Main loop consuming jobs from Redis."""
        log.info("Worker loop started")
        while self.is_running and self.client:
            try:
                # BLPOP blocks until an item is available (timeout=1s to allow shutdown check)
                item = await self.client.blpop(JOB_QUEUE_KEY, timeout=1)
                
                if not item:
                    continue

                # item is tuple (key, value)
                _, job_json = item
                job = json.loads(job_json)
                job_name = job.get("name")
                payload = job.get("payload")

                handler = self.handlers.get(job_name)
                if handler:
                    log.info(f"Processing job: {job_name}")
                    try:
                        await handler(payload)
                        log.info(f"Job complete: {job_name}")
                    except Exception as exc:
                        log.error(f"Job failed: {job_name} — {exc}", exc_info=True)
                else:
                    log.warning(f"No handler for job: {job_name}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Worker loop error: {e}")
                await asyncio.sleep(1) # Backoff on error

    async def shutdown(self):
        self.is_running = False
        if self.client:
            await self.client.close()


# Singleton accessor
def get_queue() -> TaskQueue:
    return TaskQueue.get_instance()
