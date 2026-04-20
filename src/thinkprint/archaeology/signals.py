"""Signal detection inside a cluster — rephrase events and acceptance signals.

These are the highest-value behavioral signals. They reveal what the user actually
prefers, not what they say they prefer.

- Rephrase event: user asks for the same thing twice with different framing
  ("make it shorter", "be more concise", "tldr"). Implies dissatisfaction with
  prior format/length.
- Acceptance signal: user says "perfect", "exactly", "thanks that worked".
  Implies the prior assistant turn nailed something.
"""

from __future__ import annotations

import re

from thinkprint.models import Message, Role

# Words/phrases that often indicate the user is correcting or refining a prior answer
_REPHRASE_CUES = (
    re.compile(r"\b(shorter|too long|tl;?dr|be brief|concise|cut it down)\b", re.I),
    re.compile(r"\b(more detail|expand|elaborate|deeper|explain more)\b", re.I),
    re.compile(r"\b(simpler|simpler way|simpler version|in plain english)\b", re.I),
    re.compile(r"\b(more formal|less casual|professional tone)\b", re.I),
    re.compile(r"\b(less formal|more casual|chill tone)\b", re.I),
    re.compile(r"\b(no bullet|no list|prose|paragraph form)\b", re.I),
    re.compile(r"\b(use bullets|bullet point|list it|itemize)\b", re.I),
    re.compile(r"\b(try again|that['']s wrong|not what i meant|misunderstood)\b", re.I),
)

_ACCEPTANCE_CUES = (
    re.compile(r"\b(perfect|exactly|nailed it|that['']s it|spot on|love it)\b", re.I),
    re.compile(r"\b(works|worked|that worked|fixed it|problem solved)\b", re.I),
    re.compile(r"\b(thanks that['']s helpful|super helpful|really helpful)\b", re.I),
    re.compile(r"\bship it\b", re.I),
)


class Signal:
    """Lightweight value object — not a Pydantic model to keep this hot path fast."""

    __slots__ = ("kind", "user_msg_id", "prior_assistant_msg_id", "excerpt")

    def __init__(self, kind: str, user_msg_id: str, prior_assistant_msg_id: str | None, excerpt: str):
        self.kind = kind
        self.user_msg_id = user_msg_id
        self.prior_assistant_msg_id = prior_assistant_msg_id
        self.excerpt = excerpt

    def __repr__(self) -> str:
        return f"Signal(kind={self.kind!r}, user={self.user_msg_id!r})"


def _last_assistant_before(messages: list[Message], idx: int) -> Message | None:
    for j in range(idx - 1, -1, -1):
        if messages[j].role == Role.ASSISTANT:
            return messages[j]
    return None


def detect_rephrase_events(messages: list[Message]) -> list[Signal]:
    """Find user messages that look like a rephrase of a prior request."""
    out: list[Signal] = []
    for i, m in enumerate(messages):
        if m.role != Role.USER:
            continue
        for pattern in _REPHRASE_CUES:
            if pattern.search(m.content):
                prior = _last_assistant_before(messages, i)
                out.append(
                    Signal(
                        kind="rephrase",
                        user_msg_id=m.id,
                        prior_assistant_msg_id=prior.id if prior else None,
                        excerpt=m.content[:160],
                    )
                )
                break
    return out


def detect_acceptance_signals(messages: list[Message]) -> list[Signal]:
    """Find user messages that explicitly endorse the prior assistant turn."""
    out: list[Signal] = []
    for i, m in enumerate(messages):
        if m.role != Role.USER:
            continue
        for pattern in _ACCEPTANCE_CUES:
            if pattern.search(m.content):
                prior = _last_assistant_before(messages, i)
                out.append(
                    Signal(
                        kind="acceptance",
                        user_msg_id=m.id,
                        prior_assistant_msg_id=prior.id if prior else None,
                        excerpt=m.content[:160],
                    )
                )
                break
    return out
