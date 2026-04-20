"""Core data models for Thinkprint.

Everything is a Pydantic model so we get free validation at every system boundary.
Immutable by convention — never mutate; always construct a new instance.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Role(str, Enum):
    """Speaker role in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Source(str, Enum):
    """Where a message or rule originated."""

    CLAUDE_MD = "claude_md"
    CLAUDE_AGENT = "claude_agent"
    CLAUDE_COMMAND = "claude_command"
    CURSOR_RULES = "cursor_rules"
    WINDSURF_RULES = "windsurf_rules"
    CHATGPT_EXPORT = "chatgpt_export"
    CLAUDE_EXPORT = "claude_export"


class Message(BaseModel):
    """A single normalized chat message from any source."""

    id: str
    conversation_id: str
    role: Role
    content: str
    created_at: datetime | None = None
    source: Source

    def __hash__(self) -> int:
        return hash(self.id)


class FilterDecision(BaseModel):
    """Result of running a message through the filter pipeline."""

    message_id: str
    keep: bool
    reason: str
    flagged_injection: bool = False
    injection_score: float = 0.0


class Cluster(BaseModel):
    """A group of related messages identified by the clusterer."""

    id: int
    label: str
    message_ids: list[str]
    keywords: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    """A pointer back to the message(s) that support a rule."""

    message_id: str
    excerpt: str
    source: Source


class RuleConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Rule(BaseModel):
    """A behavioral rule extracted from the user's history.

    Tier 1 rules come straight from config files (CLAUDE.md etc) — explicit, no inference.
    Tier 2 rules are synthesized from chat-history clusters — inferred from behavior.
    """

    id: str
    topic: str
    statement: str
    tier: Literal[1, 2]
    confidence: RuleConfidence
    evidence: list[Evidence] = Field(default_factory=list)
    source_cluster_id: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_markdown(self) -> str:
        """Render a single rule as a markdown block with evidence inline."""
        lines = [
            f"### {self.statement}",
            f"*Topic: `{self.topic}` · Tier {self.tier} · Confidence: {self.confidence.value}*",
            "",
        ]
        if self.evidence:
            lines.append("**Evidence:**")
            for ev in self.evidence[:3]:  # cap at 3 to keep output readable
                excerpt = ev.excerpt.strip().replace("\n", " ")
                if len(excerpt) > 200:
                    excerpt = excerpt[:200] + "..."
                lines.append(f"- `{ev.source.value}`: {excerpt}")
            lines.append("")
        return "\n".join(lines)
