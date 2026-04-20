"""Archaeology — cluster messages by topic, detect signals, synthesize Tier 2 rules."""

from thinkprint.archaeology.clusterer import cluster_messages
from thinkprint.archaeology.signals import detect_acceptance_signals, detect_rephrase_events
from thinkprint.archaeology.synthesizer import synthesize_rules

__all__ = [
    "cluster_messages",
    "detect_acceptance_signals",
    "detect_rephrase_events",
    "synthesize_rules",
]
