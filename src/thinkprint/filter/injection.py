"""Layer-1 injection detection (heuristic only, no classifier in MVP).

Critical rule from the spec: USER messages are signals, not threats. Injection risk
lives in ASSISTANT messages where uploaded data could be impersonating instructions.

We flag candidates but never hard-delete. The spec calls for soft quarantine and user
review — for the MVP CLI we surface a count and tag the messages so downstream code
can include or skip them via flag.
"""

from __future__ import annotations

import re

from thinkprint.models import FilterDecision, Message, Role

# Heuristic patterns — high recall, modest precision. The MVP intentionally keeps
# the classifier (Layer 2) and context-window check (Layer 3) out of scope.
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|prompts?)\b", re.I),
    re.compile(r"\bdisregard\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)\b", re.I),
    re.compile(r"\byou\s+are\s+now\s+(a|an)\s+\w+", re.I),
    re.compile(r"\bact\s+as\s+(if\s+you\s+are\s+)?(a|an)\s+\w+", re.I),
    re.compile(r"\bsystem\s*:\s*(?=\S)", re.I),
    re.compile(r"</?\s*system\s*>", re.I),
    re.compile(r"\bjailbreak\b", re.I),
    re.compile(r"\bDAN\s+mode\b"),
)

# When the user is clearly *quoting* or *describing* injection, score lower.
_DEFENSIVE_CONTEXT = re.compile(
    r"\b(prompt\s+injection|jailbreak|attack|security|vulnerab|defense|guardrail)\b", re.I
)


def _score(content: str, role: Role) -> float:
    """Rough 0-1 injection probability for the MVP (no real classifier yet)."""
    hits = sum(1 for p in _INJECTION_PATTERNS if p.search(content))
    if hits == 0:
        return 0.0

    base = min(0.5 + 0.15 * hits, 0.95)

    # User messages discussing the topic of injection get heavily discounted.
    if role == Role.USER and _DEFENSIVE_CONTEXT.search(content):
        base *= 0.3
    # Assistant messages are the actual threat surface — don't discount them.
    elif role == Role.ASSISTANT:
        base = min(base + 0.1, 0.95)

    return round(base, 3)


def flag_injection_candidates(messages: list[Message]) -> list[FilterDecision]:
    """Return one FilterDecision per message, with injection scoring populated.

    `keep` stays True — soft quarantine philosophy: never hard-block here. Downstream
    code can choose to exclude messages above a threshold when sending to the LLM.
    """
    decisions: list[FilterDecision] = []
    for m in messages:
        score = _score(m.content, m.role)
        flagged = score >= 0.6
        decisions.append(
            FilterDecision(
                message_id=m.id,
                keep=True,
                reason="injection_flagged" if flagged else "clean",
                flagged_injection=flagged,
                injection_score=score,
            )
        )
    return decisions
