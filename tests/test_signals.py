"""Tests for rephrase + acceptance signal detection and clustering."""

from __future__ import annotations

from thinkprint.archaeology import (
    cluster_messages,
    detect_acceptance_signals,
    detect_rephrase_events,
)


def test_detect_rephrase_events(sample_messages):
    signals = detect_rephrase_events(sample_messages)
    assert len(signals) == 1
    assert signals[0].kind == "rephrase"
    assert signals[0].user_msg_id == "m3"
    # Rephrase should reference the prior assistant message
    assert signals[0].prior_assistant_msg_id == "m2"


def test_detect_acceptance_signals(sample_messages):
    signals = detect_acceptance_signals(sample_messages)
    assert len(signals) == 1
    assert signals[0].kind == "acceptance"
    assert signals[0].user_msg_id == "m5"
    assert signals[0].prior_assistant_msg_id == "m4"


def test_cluster_messages_returns_clusters(sample_messages):
    clusters = cluster_messages(sample_messages)
    assert clusters, "should produce at least one cluster"
    # Total message ids across all clusters equals input count
    all_ids = [mid for c in clusters for mid in c.message_ids]
    assert len(all_ids) == len(sample_messages)


def test_cluster_messages_handles_empty():
    assert cluster_messages([]) == []
