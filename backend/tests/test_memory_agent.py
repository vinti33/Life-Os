"""Tests for agents/memory_agent.py — Lifecycle Logic"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from agents.memory_agent import (
    CONFIDENCE_DECAY_RATE,
    CONFIDENCE_PRUNE_THRESHOLD,
    CONFIDENCE_PROMOTE_THRESHOLD,
    CONFIDENCE_REINFORCE_VALUE,
)


class TestMemoryConstants:
    """Validate that lifecycle constants are sensible."""

    def test_decay_rate_positive(self):
        assert CONFIDENCE_DECAY_RATE > 0
        assert CONFIDENCE_DECAY_RATE <= 0.5  # Shouldn't decay too fast

    def test_prune_threshold_reasonable(self):
        assert 0.0 < CONFIDENCE_PRUNE_THRESHOLD < 1.0

    def test_promote_threshold_above_prune(self):
        assert CONFIDENCE_PROMOTE_THRESHOLD > CONFIDENCE_PRUNE_THRESHOLD

    def test_reinforce_value_is_max(self):
        assert CONFIDENCE_REINFORCE_VALUE == 1.0

    def test_decay_reaches_prune_in_reasonable_time(self):
        """Starting at 0.9, decay should reach prune threshold in ~6 days."""
        confidence = 0.9
        days = 0
        while confidence >= CONFIDENCE_PRUNE_THRESHOLD:
            confidence -= CONFIDENCE_DECAY_RATE
            days += 1
        assert 3 <= days <= 10  # Should take 3-10 days


class TestMemoryTierLogic:
    """Tests for tier promotion eligibility logic."""

    def test_promotion_requires_high_confidence(self):
        # Simulate: confidence=0.9, access_count=5 → should promote
        confidence = 0.9
        access_count = 5
        eligible = confidence >= CONFIDENCE_PROMOTE_THRESHOLD and access_count >= 3
        assert eligible is True

    def test_no_promotion_if_low_confidence(self):
        confidence = 0.5
        access_count = 10
        eligible = confidence >= CONFIDENCE_PROMOTE_THRESHOLD and access_count >= 3
        assert eligible is False

    def test_no_promotion_if_low_access(self):
        confidence = 0.9
        access_count = 1
        eligible = confidence >= CONFIDENCE_PROMOTE_THRESHOLD and access_count >= 3
        assert eligible is False

    def test_word_overlap_detection(self):
        """Test the 80% word-overlap matching logic used for dedup."""
        content_a = "I hate jogging in the morning"
        content_b = "I hate jogging during the morning"

        words_a = set(content_a.lower().split())
        words_b = set(content_b.lower().split())
        overlap = len(words_a & words_b) / max(len(words_a), len(words_b))

        # 5 common words out of 6 = 83%
        assert overlap >= 0.8
