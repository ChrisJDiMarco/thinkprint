"""Tier 2 rule synthesis — call Claude on a per-cluster basis to derive behavioral rules.

Per the spec: never feed all chat history to one LLM call. Cluster first, then make one
focused call per cluster. Each call sees the cluster's representative messages plus any
detected signals, and returns a JSON array of rules with evidence pointers.

If no API key is available, this module returns an empty list and lets the caller fall
back to Tier 1 only — Thinkprint still produces useful output.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from thinkprint.archaeology.signals import Signal
from thinkprint.models import Cluster, Evidence, Message, Rule, RuleConfidence

_DEFAULT_MODEL = "claude-sonnet-4-6"
_MAX_MESSAGES_PER_CALL = 40
_MAX_CHARS_PER_MESSAGE = 600

_SYSTEM_PROMPT = """You are an expert behavioral analyst. Given a cluster of chat messages
between a user and an AI assistant, derive concrete preference rules about HOW THIS
USER WORKS — the kind of calibration the next assistant would want to know.

## Rule typology (every rule must fit one axis)

Each rule belongs to exactly one axis. Tagging the axis keeps the output load-bearing
instead of vague.

  LENGTH       — how long should responses be, when to truncate
  FORMALITY    — tone, voice, register, profanity tolerance
  STRUCTURE    — prose vs bullets, lead with answer vs reasoning, summaries
  FORMAT       — markdown/docx/pdf/html defaults, save locations, delivery norms
  PLANNING     — plan-first vs jump-in, when to ask clarifying questions
  CORRECTION   — how the user signals stop/continue, tolerance for pushback
  TOOLS        — preferred apps, connectors, OS, integrations
  DOMAIN       — vocabulary, role, what they build, stakeholders
  SCOPE        — minimal vs expansive, touch-adjacent-files tolerance

Prefix every rule statement with its axis tag in brackets, e.g.
  "[STRUCTURE] Lead with the answer; no trailing summaries."

## Root-cause rule on REPHRASE events

If the payload contains REPHRASE EVENTS, treat each as a signal that the assistant's
prior turn missed the mark. For each rephrase, ask: what rule, if followed, would
have prevented this correction? Prefer rules rooted in rephrases over rules derived
from neutral exchanges — rephrases are the highest-signal evidence you have.

## Acceptance signals

ACCEPTANCE SIGNALS (user endorsed the prior turn) are positive evidence. A pattern
that appears before 2+ acceptances earns a rule. A one-off "ok thanks" does not.

## Anchored confidence criteria

Use these thresholds — don't vibe-grade:

  high    — ≥3 independent turns of evidence pointing the same way, OR 1 rephrase + 1
            explicit restatement of the preference in the user's own words.
  medium  — 2 turns of evidence, or 1 rephrase alone.
  low     — 1 turn of evidence. (Still emit the rule; the caller will weight it.)

If evidence is contradictory across turns, DO NOT emit a rule for that axis — let
the ambiguity surface downstream instead of forcing a false resolution.

## Rule quality requirements

- Derivable from the evidence shown (cite indices; no hallucination).
- Behavioral, not identity ("prefers terse replies" not "is a terse person").
- Actionable for an AI assistant calibrating its next response.
- One declarative sentence, 20–200 chars after the axis tag.
- Use the user's own language where it survives in the transcript.

## Output schema

Output ONLY a JSON array. No prose, no markdown fence, no preamble. Each item:
{
  "statement": "[AXIS] Short imperative-style rule",
  "confidence": "high|medium|low",
  "evidence_message_indices": [int, ...]
}

The evidence_message_indices MUST reference the `[i]` indices shown in the payload.
If no reliable rule can be derived from the cluster, return [].
"""


def _make_rule_id(topic: str, statement: str) -> str:
    return "tier2_" + hashlib.sha1(f"{topic}|{statement}".encode("utf-8")).hexdigest()[:12]


def _truncate(text: str) -> str:
    text = text.strip()
    if len(text) > _MAX_CHARS_PER_MESSAGE:
        return text[:_MAX_CHARS_PER_MESSAGE] + "…"
    return text


def _build_user_prompt(
    cluster: Cluster,
    cluster_messages: list[Message],
    rephrases: list[Signal],
    acceptances: list[Signal],
) -> str:
    lines: list[str] = [
        f"CLUSTER TOPIC: {cluster.label}",
        f"KEYWORDS: {', '.join(cluster.keywords) if cluster.keywords else '(none)'}",
        "",
        "MESSAGES:",
    ]
    sample = cluster_messages[:_MAX_MESSAGES_PER_CALL]
    for i, m in enumerate(sample):
        lines.append(f"[{i}] {m.role.value}: {_truncate(m.content)}")

    if rephrases:
        lines.append("")
        lines.append("REPHRASE EVENTS DETECTED (user corrected/refined prior turn):")
        for s in rephrases[:5]:
            lines.append(f"  - {s.excerpt}")
    if acceptances:
        lines.append("")
        lines.append("ACCEPTANCE SIGNALS DETECTED (user endorsed prior turn):")
        for s in acceptances[:5]:
            lines.append(f"  - {s.excerpt}")

    lines.append("")
    lines.append("Derive behavioral rules now. JSON array only.")
    return "\n".join(lines)


def _parse_response(raw: str) -> list[dict[str, Any]]:
    """Tolerant JSON-array parser — strips code fences if the model added any."""
    text = raw.strip()
    if text.startswith("```"):
        # remove first ```json or ``` line and trailing ```
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _call_claude(system: str, user: str, model: str) -> str:
    """Wrap the Anthropic SDK call. Imported lazily so the package imports without it."""
    try:
        import anthropic  # noqa: WPS433 (intentional lazy import)
    except ImportError as exc:  # pragma: no cover - environment issue
        raise RuntimeError("anthropic SDK not installed") from exc

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts)


def synthesize_rules(
    cluster: Cluster,
    messages: list[Message],
    rephrases: list[Signal],
    acceptances: list[Signal],
    model: str = _DEFAULT_MODEL,
) -> list[Rule]:
    """Call Claude once per cluster and convert response into Rule objects.

    Returns [] if no API key is set or if the model returns nothing parseable.
    The caller must filter `messages` to this cluster's IDs before calling.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return []
    if not messages:
        return []

    user_prompt = _build_user_prompt(cluster, messages, rephrases, acceptances)
    try:
        raw = _call_claude(_SYSTEM_PROMPT, user_prompt, model)
    except Exception:  # broad: caller decides what to log; we just degrade
        return []

    items = _parse_response(raw)
    out: list[Rule] = []
    msg_by_index = {i: m for i, m in enumerate(messages[:_MAX_MESSAGES_PER_CALL])}

    for item in items:
        statement = (item.get("statement") or "").strip()
        if len(statement) < 8 or len(statement) > 280:
            continue
        confidence_raw = (item.get("confidence") or "medium").lower()
        try:
            confidence = RuleConfidence(confidence_raw)
        except ValueError:
            confidence = RuleConfidence.MEDIUM

        evidence_indices = item.get("evidence_message_indices") or []
        evidence: list[Evidence] = []
        if isinstance(evidence_indices, list):
            for idx in evidence_indices:
                if isinstance(idx, int) and idx in msg_by_index:
                    m = msg_by_index[idx]
                    evidence.append(
                        Evidence(
                            message_id=m.id,
                            excerpt=_truncate(m.content),
                            source=m.source,
                        )
                    )

        out.append(
            Rule(
                id=_make_rule_id(cluster.label, statement),
                topic=cluster.label,
                statement=statement,
                tier=2,
                confidence=confidence,
                evidence=evidence,
                source_cluster_id=cluster.id,
            )
        )
    return out
