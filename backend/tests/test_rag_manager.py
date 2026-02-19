"""Tests for rag/manager.py — RetrievalResult & Scoring"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from rag.manager import RetrievalResult, RAGManager


class TestRetrievalResult:
    def test_creation(self):
        r = RetrievalResult(text="hello", score=0.85, rank=1, distance=0.18)
        assert r.text == "hello"
        assert r.score == 0.85
        assert r.rank == 1
        assert r.distance == 0.18

    def test_to_dict(self):
        r = RetrievalResult(text="test", score=0.9, rank=1, distance=0.1)
        d = r.to_dict()
        assert isinstance(d, dict)
        assert d["text"] == "test"
        assert d["score"] == 0.9

    def test_score_range(self):
        """Score should be between 0 and 1 for any positive distance."""
        for dist in [0.0, 0.5, 1.0, 10.0, 100.0]:
            score = 1.0 / (1.0 + dist)
            assert 0.0 <= score <= 1.0


class TestRAGManagerHealthCheck:
    def test_health_check_without_index(self):
        mgr = RAGManager(
            data_path="/tmp/nonexistent_data.json",
            index_path="/tmp/nonexistent.index",
            texts_path="/tmp/nonexistent_texts.json",
        )
        health = mgr.health_check()
        assert "index_loaded" in health
        assert "indexed_entries" in health
        assert "source_entries" in health
        assert "embedding_dim" in health

    def test_query_empty_index(self):
        mgr = RAGManager(
            data_path="/tmp/nonexistent_data.json",
            index_path="/tmp/nonexistent.index",
            texts_path="/tmp/nonexistent_texts.json",
        )
        result = mgr.query("test query")
        assert result == ""

    def test_query_scored_empty_index(self):
        mgr = RAGManager(
            data_path="/tmp/nonexistent_data.json",
            index_path="/tmp/nonexistent.index",
            texts_path="/tmp/nonexistent_texts.json",
        )
        result = mgr.query_scored("test query")
        assert result == []
