"""Noise removal — drop messages with no behavioral signal.

Heuristic only, no LLM. Cheap to run on every message.
Greetings, single-word acknowledgments, very short messages, and obvious
session-metadata strings get dropped. Keeps everything substantive.
"""

from __future__ import annotations

import re

from thinkprint.models import FilterDecision, Message

# Compiled once. Order matters — most-specific first.
_NOISE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\s*(hi|hey|hello|yo|sup|good\s*morning|good\s*night)[!.\s]*$", re.I), "greeting"),
    (re.compile(r"^\s*(thanks|thank\s*you|ty|tysm|thx|cheers)[!.\s]*$", re.I), "ack"),
    (re.compile(r"^\s*(ok|okay|cool|nice|got\s*it|sounds\s*good|yes|no|sure|yep|nope)[!.\s]*$", re.I), "ack"),
    (re.compile(r"^\s*(lol|lmao|haha|hmm+|huh|wow)[!.\s]*$", re.I), "filler"),
    (re.compile(r"^\s*\[\s*image\s*\]\s*$", re.I), "media_placeholder"),
    (re.compile(r"^\s*$"), "empty"),
)

# Below this many non-whitespace characters we drop unless flagged otherwise
_MIN_CONTENT_CHARS = 12


def is_noise(content: str) -> tuple[bool, str]:
    """Return (is_noise, reason)."""
    for pattern, reason in _NOISE_PATTERNS:
        if pattern.match(content):
            return True, reason
    if len(content.strip()) < _MIN_CONTENT_CHARS:
        return True, "too_short"
    return False, "kept"


def strip_noise(messages: list[Message]) -> tuple[list[Message], list[FilterDecision]]:
    """Filter a message stream. Return (kept_messages, decisions_for_all)."""
    kept: list[Message] = []
    decisions: list[FilterDecision] = []
    for m in messages:
        noise, reason = is_noise(m.content)
        decisions.append(FilterDecision(message_id=m.id, keep=not noise, reason=reason))
        if not noise:
            kept.append(m)
    return kept, decisions
