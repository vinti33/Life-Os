"""
LifeOS RAG Manager — Vector Retrieval with Relevance Scoring
=============================================================
Manages a FAISS index for semantic search across user memories
and knowledge base entries. Implements singleton caching, multi-result
retrieval with deduplication, relevance scoring, and index health monitoring.
"""

import os
import json
import faiss
import requests
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from config import settings
from utils.logger import get_logger, timed, RAGError
from utils.cache import cache
from utils.queue import get_queue

log = get_logger("rag")

# Global singleton instance
_GLOBAL_RAG_INSTANCE = None


# ---------------------------------------------------------------------------
# Retrieval Result
# ---------------------------------------------------------------------------
@dataclass
class RetrievalResult:
    """A single retrieval result with relevance metadata."""
    text: str
    score: float   # 0.0–1.0, higher = more relevant
    rank: int      # 1-based position
    distance: float  # Raw L2 distance from FAISS

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# RAG Manager
# ---------------------------------------------------------------------------
class RAGManager:
    EMBEDDING_DIM = 768  # nomic-embed-text default

    def __init__(
        self,
        data_path: str = "rag/data.json",
        index_path: str = "rag/data.index",
        texts_path: str = "rag/texts.json",
    ):
        self.data_path = data_path
        self.index_path = index_path
        self.texts_path = texts_path
        self.index: Optional[faiss.IndexFlatL2] = None
        self.texts: List[str] = []

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------
    async def _embed(self, text: str) -> np.ndarray:
        """Generates a vector embedding via the Ollama embeddings endpoint."""
        base_url = settings.OPENAI_BASE_URL.replace("/v1", "")
        
        def _sync_request():
            try:
                r = requests.post(
                    f"{base_url}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text},
                    timeout=10,
                )
                r.raise_for_status()
                return np.array(r.json()["embedding"], dtype="float32")
            except Exception as e:
                log.warning(f"Embedding failed, returning zero vector: {e}")
                return np.zeros(self.EMBEDDING_DIM, dtype="float32")

        return await asyncio.to_thread(_sync_request)

    # ------------------------------------------------------------------
    # Index Management
    # ------------------------------------------------------------------


    # Helper for sync context
    def _embed_sync(self, text: str) -> np.ndarray:
         base_url = settings.OPENAI_BASE_URL.replace("/v1", "")
         try:
            r = requests.post(
                f"{base_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=10,
            )
            r.raise_for_status()
            return np.array(r.json()["embedding"], dtype="float32")
         except Exception as e:
            log.warning(f"Embedding failed, returning zero vector: {e}")
            return np.zeros(self.EMBEDDING_DIM, dtype="float32")

    def rebuild_index(self):
        """Rebuilds the FAISS index from the source data.json file."""
        if not os.path.exists(self.data_path):
            log.warning(f"Data file {self.data_path} not found — skipping rebuild")
            return

        with open(self.data_path, "r") as f:
            data = json.load(f)

        vectors = []
        self.texts = []

        for item in data:
            if not item.get("text", "").strip():
                continue
            log.debug(f"Embedding: {item['text'][:50]}...")
            vec = self._embed_sync(item["text"])
            vectors.append(vec)
            self.texts.append(item["text"])

        if not vectors:
            return

        vectors = np.array(vectors)
        dim = vectors.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(vectors)

        faiss.write_index(self.index, self.index_path)
        with open(self.texts_path, "w") as f:
            json.dump(self.texts, f)
        log.info(f"Index rebuilt: {len(self.texts)} entries, dim={dim}")

    async def load_index(self):
        """Loads index and texts into memory (no-op if already loaded)."""
        if self.index is not None and self.texts:
            return

        if os.path.exists(self.index_path) and os.path.exists(self.texts_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.texts_path, "r") as f:
                    self.texts = json.load(f)

                # Auto-rebuild if source has more entries than index
                if os.path.exists(self.data_path):
                    def _check_stale():
                        with open(self.data_path, "r") as f:
                            return len(json.load(f))
                    
                    source_count = await asyncio.to_thread(_check_stale)
                    if source_count > len(self.texts):
                        log.warning(f"Index stale ({len(self.texts)} indexed vs {source_count} in source) — rebuilding")
                        await asyncio.to_thread(self.rebuild_index)
                        return

                log.info(f"RAG index loaded: {len(self.texts)} entries")
            except Exception as e:
                log.error(f"Failed to load index: {e}")
                await asyncio.to_thread(self.rebuild_index)
        else:
            log.info("No existing index found — rebuilding from source")
            await asyncio.to_thread(self.rebuild_index)

    # ...

    # ------------------------------------------------------------------
    # Query — Multi-result with relevance scoring
    # ------------------------------------------------------------------
    @cache(ttl=600, key_prefix="rag:query")
    async def query(self, text: str, k: int = 3) -> str:
        """
        Returns the top-k most relevant text chunks, deduplicated.
        Falls back to empty string if index is unavailable.
        """
        await self.load_index()
        if self.index is None or not self.texts:
            return ""

        try:
            q_vec = await self._embed(text)
            # FAISS search is fast in-memory, ok to keep sync
            D, I = self.index.search(np.array([q_vec]), k=min(k, len(self.texts)))

            results = []
            seen = set()
            for rank, (idx, dist) in enumerate(zip(I[0], D[0])):
                if idx == -1 or idx >= len(self.texts):
                    continue
                chunk = self.texts[idx]
                if chunk in seen:
                    continue
                seen.add(chunk)

                score = 1.0 / (1.0 + float(dist))
                results.append(RetrievalResult(
                    text=chunk,
                    score=round(score, 4),
                    rank=rank + 1,
                    distance=round(float(dist), 4),
                ))

            if results:
                log.info(f"RAG query returned {len(results)} results (top score={results[0].score})")

            return "\n".join(r.text for r in results)
        except Exception as e:
            log.error(f"RAG query failed: {e}")
            return ""

    def query_scored(self, text: str, k: int = 3) -> List[RetrievalResult]:
        """Returns structured retrieval results with scores — for programmatic use."""
        self.load_index()
        if self.index is None or not self.texts:
            return []

        try:
            q_vec = self._embed_sync(text)
            D, I = self.index.search(np.array([q_vec]), k=min(k, len(self.texts)))

            results = []
            seen = set()
            for rank, (idx, dist) in enumerate(zip(I[0], D[0])):
                if idx == -1 or idx >= len(self.texts):
                    continue
                chunk = self.texts[idx]
                if chunk in seen:
                    continue
                seen.add(chunk)

                score = 1.0 / (1.0 + float(dist))
                results.append(RetrievalResult(
                    text=chunk,
                    score=round(score, 4),
                    rank=rank + 1,
                    distance=round(float(dist), 4),
                ))
            return results
        except Exception as e:
            log.error(f"Scored query failed: {e}")
            return []

    # ------------------------------------------------------------------
    # Memory Addition
    # ------------------------------------------------------------------

    def add_memory(self, text: str, use_queue: bool = True):
        """Adds a single memory to disk and the live FAISS index."""

        # Try queueing background job first
        if use_queue:
            queue = get_queue()
            if queue.is_running:
                import asyncio
                # Fire and forget via queue
                asyncio.create_task(queue.enqueue("rag:add_memory", text))
                return

        # Direct execution fallback (or worker execution path)
        self._add_memory_sync(text)

    async def add_memory_job(self, text: str):
        """Async wrapper for background job execution."""
        await asyncio.to_thread(self._add_memory_sync, text)

    def _add_memory_sync(self, text: str):
        """Internal synchronous method for adding memory - used by worker."""
        # Append to JSON source
        if os.path.exists(self.data_path):
            with open(self.data_path, "r+") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []
                data.append({"text": text, "source": "user_memory"})
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)

        self.load_index()
        if self.index is not None:
            vec = self._embed_sync(text)
            self.index.add(np.array([vec]))
            self.texts.append(text)

            # Persist updated index
            faiss.write_index(self.index, self.index_path)
            with open(self.texts_path, "w") as f:
                json.dump(self.texts, f)
            log.info(f"Memory added and indexed: '{text[:40]}...'")

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------
    def health_check(self) -> Dict[str, Any]:
        """Returns diagnostic info about the RAG index."""
        self.load_index()
        source_count = 0
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r") as f:
                    source_count = len(json.load(f))
            except Exception:
                pass

        return {
            "index_loaded": self.index is not None,
            "indexed_entries": len(self.texts),
            "source_entries": source_count,
            "index_stale": source_count > len(self.texts),
            "embedding_dim": self.EMBEDDING_DIM,
            "index_file": self.index_path,
        }


# ---------------------------------------------------------------------------
# Singleton Factory
# ---------------------------------------------------------------------------
def get_rag_manager() -> RAGManager:
    """Returns the singleton RAGManager instance."""
    global _GLOBAL_RAG_INSTANCE
    if _GLOBAL_RAG_INSTANCE is None:
        _GLOBAL_RAG_INSTANCE = RAGManager()
        # Note: Index loading happens on first query to avoid blocking main thread

        # Register queue handler for background jobs
        queue = get_queue()
        queue.register_handler("rag:add_memory", _GLOBAL_RAG_INSTANCE.add_memory_job)

        log.info("Singleton RAGManager created and index pre-loaded")
    return _GLOBAL_RAG_INSTANCE


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    manager = RAGManager(
        data_path="data.json",
        index_path="data.index",
        texts_path="texts.json",
    )
    manager.rebuild_index()
    print(json.dumps(manager.health_check(), indent=2))
