"""
LifeOS Memory Agent — Lifecycle-Managed Fact Extraction
========================================================
Extracts permanent facts from chat messages, manages short-term
vs long-term memory tiers, implements confidence decay, and provides
prioritized context retrieval for downstream agents.
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional
from beanie import PydanticObjectId
from openai import AsyncOpenAI
from config import settings
from models import UserMemory, MemoryTier
from rag.manager import RAGManager
from utils.logger import get_logger, timed

log = get_logger("memory_agent")

# Confidence thresholds
CONFIDENCE_DECAY_RATE = 0.1       # Per day without access
CONFIDENCE_PRUNE_THRESHOLD = 0.3  # Below this → prune
CONFIDENCE_PROMOTE_THRESHOLD = 0.8  # Above this + 3 accesses → promote to long-term
CONFIDENCE_REINFORCE_VALUE = 1.0  # Reset to this when reinforced


class MemoryAgent:
    def __init__(self, rag_manager: RAGManager):
        # Use requests to avoid IPv6 issues
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        self.rag_manager = rag_manager

    # ------------------------------------------------------------------
    # Extraction — Runs as a BackgroundTask from chat router
    # ------------------------------------------------------------------
    @timed("memory_agent")
    async def extract_and_save(self, user_id: PydanticObjectId, message_content: str):
        """
        Analyzes the user message for permanent facts.
        If found, checks for duplicates, reinforces or creates new memory.
        """
        system_prompt = """
You are a Memory Extractor. Identify PERMANENT user facts from the message.

FACT TYPES:
- constraint ("I work 9-5", "I sleep at 10pm")
- preference ("I hate jogging", "I love sci-fi")
- goal ("I want to learn French", "Save $5000 this year")

IGNORE: temporary states, questions, commands, greetings.

OUTPUT (JSON ONLY):
{
    "found": true/false,
    "fact": "extracted statement",
    "category": "constraint|preference|goal"
}
"""
        import requests
        import asyncio

        def _sync_request():
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": settings.AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt.strip()},
                    {"role": "user", "content": message_content},
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 200,
            }
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            r.raise_for_status()
            return r.json()

        try:
            response = await asyncio.to_thread(_sync_request)
            data = json.loads(response["choices"][0]["message"]["content"])

            if not data.get("found"):
                log.debug(f"No extractable fact in: '{message_content[:40]}...'")
                return

            content = data["fact"]
            category = data.get("category", "preference")

            # Check for existing similar memory (reinforce instead of duplicate)
            existing = await self._find_similar_memory(user_id, content)
            if existing:
                await self._reinforce_memory(existing)
                log.info(f"Memory reinforced: '{content[:40]}...' (confidence → {existing.confidence})")
                return

            # Create new memory (starts as short-term)
            memory = UserMemory(
                user_id=user_id,
                content=content,
                category=category,
                tier=MemoryTier.SHORT_TERM,
                source="chat",
                confidence=0.9,
                access_count=0,
            )
            await memory.insert()

            # Also add to RAG index
            self.rag_manager.add_memory(content)
            log.info(f"New memory saved: [{category}] '{content[:50]}...'")

        except Exception as e:
            log.error(f"Memory extraction failed: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Memory Retrieval — Prioritized by confidence × recency
    # ------------------------------------------------------------------
    @timed("memory_agent")
    async def get_prioritized_context(self, user_id: PydanticObjectId, limit: int = 10) -> List[dict]:
        """
        Returns memories sorted by (confidence × recency_weight), highest first.
        Updates access timestamps on retrieved memories.
        """
        memories = await UserMemory.find(
            UserMemory.user_id == user_id,
            UserMemory.confidence >= CONFIDENCE_PRUNE_THRESHOLD,
        ).to_list()

        now = datetime.utcnow()
        scored = []
        for m in memories:
            days_since_access = max((now - m.last_accessed).days, 0)
            recency_weight = 1.0 / (1.0 + days_since_access * 0.1)
            priority = m.confidence * recency_weight
            scored.append((priority, m))

        # Sort descending by priority
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:limit]

        # Update access count and timestamp
        for _, m in top:
            m.last_accessed = now
            m.access_count += 1
            await m.save()

        log.info(f"Retrieved {len(top)} prioritized memories for user={user_id}")
        return [
            {
                "content": m.content,
                "category": m.category,
                "confidence": round(priority, 3),
                "tier": m.tier,
            }
            for priority, m in top
        ]

    # ------------------------------------------------------------------
    # Lifecycle Management
    # ------------------------------------------------------------------
    @timed("memory_agent")
    async def decay_confidence(self, user_id: PydanticObjectId):
        """
        Applies daily confidence decay to short-term memories.
        Long-term memories are exempt from decay.
        """
        short_term = await UserMemory.find(
            UserMemory.user_id == user_id,
            UserMemory.tier == MemoryTier.SHORT_TERM,
        ).to_list()

        now = datetime.utcnow()
        decayed = 0
        for m in short_term:
            days_idle = max((now - m.last_accessed).days, 0)
            if days_idle > 0:
                new_confidence = max(0.0, m.confidence - (CONFIDENCE_DECAY_RATE * days_idle))
                if new_confidence != m.confidence:
                    m.confidence = round(new_confidence, 3)
                    await m.save()
                    decayed += 1

        log.info(f"Confidence decay applied: {decayed}/{len(short_term)} memories affected")

    @timed("memory_agent")
    async def prune_stale_memories(self, user_id: PydanticObjectId) -> int:
        """
        Removes short-term memories whose confidence has dropped
        below the prune threshold. Long-term memories are never pruned.
        """
        stale = await UserMemory.find(
            UserMemory.user_id == user_id,
            UserMemory.tier == MemoryTier.SHORT_TERM,
            UserMemory.confidence < CONFIDENCE_PRUNE_THRESHOLD,
        ).to_list()

        count = len(stale)
        for m in stale:
            log.debug(f"Pruning stale memory: '{m.content[:40]}...' (confidence={m.confidence})")
            await m.delete()

        if count:
            log.info(f"Pruned {count} stale memories for user={user_id}")
        return count

    @timed("memory_agent")
    async def promote_memories(self, user_id: PydanticObjectId) -> int:
        """
        Promotes high-confidence, frequently-accessed short-term memories
        to long-term tier (permanent).
        """
        candidates = await UserMemory.find(
            UserMemory.user_id == user_id,
            UserMemory.tier == MemoryTier.SHORT_TERM,
            UserMemory.confidence >= CONFIDENCE_PROMOTE_THRESHOLD,
        ).to_list()

        promoted = 0
        for m in candidates:
            if m.access_count >= 3:
                m.tier = MemoryTier.LONG_TERM
                await m.save()
                promoted += 1
                log.info(f"Memory promoted to LONG_TERM: '{m.content[:40]}...'")

        return promoted

    @timed("memory_agent")
    async def run_lifecycle(self, user_id: PydanticObjectId):
        """
        Complete lifecycle pass: decay → prune → promote.
        Designed to run as a daily cron job.
        """
        log.info(f"=== MEMORY LIFECYCLE START === user={user_id}")
        await self.decay_confidence(user_id)
        pruned = await self.prune_stale_memories(user_id)
        promoted = await self.promote_memories(user_id)
        log.info(f"=== MEMORY LIFECYCLE COMPLETE === pruned={pruned}, promoted={promoted}")

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------
    async def _find_similar_memory(self, user_id: PydanticObjectId, content: str) -> Optional[UserMemory]:
        """
        Checks if a memory with very similar content already exists.
        Uses simple substring matching for now (RAG-based similarity could be added later).
        """
        existing = await UserMemory.find(
            UserMemory.user_id == user_id
        ).to_list()

        content_lower = content.lower().strip()
        for m in existing:
            if m.content.lower().strip() == content_lower:
                return m
            # Partial match: if 80%+ of words overlap
            content_words = set(content_lower.split())
            memory_words = set(m.content.lower().split())
            if content_words and memory_words:
                overlap = len(content_words & memory_words) / max(len(content_words), len(memory_words))
                if overlap >= 0.8:
                    return m
        return None

    async def _reinforce_memory(self, memory: UserMemory):
        """Boosts confidence and updates access tracking for an existing memory."""
        memory.confidence = min(CONFIDENCE_REINFORCE_VALUE, memory.confidence + 0.2)
        memory.access_count += 1
        memory.last_accessed = datetime.utcnow()
        await memory.save()
