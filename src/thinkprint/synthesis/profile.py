"""Profile synthesizer — turns an interview transcript into a Thinkprint.

The output is a structured markdown document with six sections:
  1. Identity
  2. Explicit preferences (from interview answers)
  3. Implicit patterns (from seed rules + answer tone)
  4. Preferred formats
  5. Working style
  6. Interview transcript (verbatim, for auditability)

Two paths:
- If ANTHROPIC_API_KEY is set, call Claude once to draft the distilled
  sections from the raw transcript + seed rules.
- If not, fall back to a deterministic template that organizes the raw
  material without LLM distillation. Still a valid Thinkprint — just
  less polished.
"""

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..interview.session import InterviewTranscript
from ..models import Rule


_DEFAULT_MODEL = "claude-sonnet-4-6"
_MAX_SEED_RULES_FOR_LLM = 60


@dataclass(frozen=True)
class SynthesisResult:
    """Output of synthesis — the sections that go into the final md."""

    identity: str
    explicit_preferences: str
    implicit_patterns: str
    preferred_formats: str
    working_style: str
    used_llm: bool


def synthesize_profile(
    transcript: InterviewTranscript,
    seed_rules: list[Rule],
    *,
    model: str = _DEFAULT_MODEL,
    api_key: str | None = None,
) -> SynthesisResult:
    """Build the six distilled sections from transcript + seed rules."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if key:
        try:
            return _synthesize_with_llm(transcript, seed_rules, model=model, api_key=key)
        except Exception as exc:  # pragma: no cover — network/api path
            # Fall back rather than fail the whole pipeline.
            return _synthesize_fallback(
                transcript,
                seed_rules,
                note=f"(LLM synthesis failed: {type(exc).__name__}; using template fallback.)",
            )
    return _synthesize_fallback(transcript, seed_rules)


def render_thinkprint_md(
    transcript: InterviewTranscript,
    result: SynthesisResult,
    *,
    user_label: str = "Thinkprint",
) -> str:
    """Render the final markdown artifact."""
    generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    rounds_count = len(transcript.rounds)
    lines = [
        f"# {user_label}",
        "",
        f"_Generated {generated} · {rounds_count} interview rounds · "
        f"{transcript.seed_rule_count} seed rules from configs_",
        "",
        "> **What this is:** a synthesized profile of how this user works, built "
        "through structured Q&A. Explicit preferences come directly from answers. "
        "Implicit patterns come from seed data (config files, prior chats) and "
        "the tone of the answers themselves.",
        "",
        "---",
        "",
        "## 1. Identity",
        "",
        result.identity.strip(),
        "",
        "## 2. Explicit preferences",
        "",
        result.explicit_preferences.strip(),
        "",
        "## 3. Implicit patterns",
        "",
        result.implicit_patterns.strip(),
        "",
        "## 4. Preferred formats",
        "",
        result.preferred_formats.strip(),
        "",
        "## 5. Working style",
        "",
        result.working_style.strip(),
        "",
        "---",
        "",
        "## 6. Interview transcript",
        "",
        _render_transcript(transcript),
        "",
    ]
    if not result.used_llm:
        lines.insert(
            6,
            "> _Note: synthesized via template fallback — set `ANTHROPIC_API_KEY` "
            "for an LLM-distilled version._",
        )
        lines.insert(7, "")
    return "\n".join(lines)


def _render_transcript(transcript: InterviewTranscript) -> str:
    blocks: list[str] = []
    for i, r in enumerate(transcript.rounds, start=1):
        block = [f"### Round {i} · {r.topic}", "", f"**Q:** {r.prompt}", "", f"**A:** {r.answer}"]
        if r.implicit_observations:
            block.extend(["", "_Implicit observations from seed data:_"])
            for obs in r.implicit_observations:
                block.append(f"- {obs}")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


# ---------------------------------------------------------------------
# LLM path
# ---------------------------------------------------------------------


_SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a profile synthesizer. You read an interview transcript and seed
    observations from a user's config files, and you produce a distilled
    profile of how this user works.

    Return strict JSON with exactly these keys, all strings, all markdown:
      identity               — 2-4 sentence paragraph on who they are and what they're building
      explicit_preferences   — bulleted list of preferences the user explicitly stated
      implicit_patterns      — bulleted list of patterns observed from seed data + answer tone
      preferred_formats      — bulleted list of format defaults (markdown, docx, pdf, etc)
      working_style          — bulleted list describing how they like to work with an AI

    Rules:
    - Never invent facts not grounded in the inputs.
    - Distinguish "they said" (explicit) from "we observed" (implicit). Do not mix them.
    - Use the user's own words when possible for explicit items.
    - Keep each section under 10 bullets. Lead with the strongest signal.
    - No trailing summaries, no meta-commentary, just the content.
    """
).strip()


def _synthesize_with_llm(
    transcript: InterviewTranscript,
    seed_rules: list[Rule],
    *,
    model: str,
    api_key: str,
) -> SynthesisResult:
    import anthropic  # type: ignore[import-not-found]

    client = anthropic.Anthropic(api_key=api_key)
    user_payload = {
        "transcript": [
            {
                "topic": r.topic,
                "question": r.prompt,
                "answer": r.answer,
                "implicit_observations": r.implicit_observations,
            }
            for r in transcript.rounds
        ],
        "seed_rules_sample": [
            {"topic": r.topic, "statement": r.statement, "tier": r.tier}
            for r in seed_rules[:_MAX_SEED_RULES_FOR_LLM]
        ],
    }
    message = client.messages.create(
        model=model,
        max_tokens=2500,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Here is the interview and seed data. Return JSON per the system prompt.\n\n"
                    + json.dumps(user_payload, indent=2)
                ),
            }
        ],
    )
    text = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )
    data = _extract_json(text)
    return SynthesisResult(
        identity=str(data.get("identity", "")).strip() or _fallback_identity(transcript),
        explicit_preferences=str(data.get("explicit_preferences", "")).strip()
        or _fallback_explicit(transcript),
        implicit_patterns=str(data.get("implicit_patterns", "")).strip()
        or _fallback_implicit(transcript, seed_rules),
        preferred_formats=str(data.get("preferred_formats", "")).strip()
        or _fallback_formats(transcript),
        working_style=str(data.get("working_style", "")).strip()
        or _fallback_working(transcript),
        used_llm=True,
    )


def _extract_json(text: str) -> dict:
    """Pull a JSON object out of a model response, tolerant of prose wrapping."""
    text = text.strip()
    if text.startswith("```"):
        # strip ```json ... ``` fences
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last-resort: try to find the first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


# ---------------------------------------------------------------------
# Template fallback
# ---------------------------------------------------------------------


def _synthesize_fallback(
    transcript: InterviewTranscript,
    seed_rules: list[Rule],
    *,
    note: str | None = None,
) -> SynthesisResult:
    identity = _fallback_identity(transcript)
    explicit = _fallback_explicit(transcript)
    implicit = _fallback_implicit(transcript, seed_rules)
    formats = _fallback_formats(transcript)
    working = _fallback_working(transcript)
    if note:
        identity = f"{note}\n\n{identity}"
    return SynthesisResult(
        identity=identity,
        explicit_preferences=explicit,
        implicit_patterns=implicit,
        preferred_formats=formats,
        working_style=working,
        used_llm=False,
    )


def _fallback_identity(transcript: InterviewTranscript) -> str:
    for r in transcript.rounds:
        if r.question_id == "identity_goals" and r.answer and r.answer != "(no answer provided)":
            return r.answer
    return "_Not captured in interview._"


def _fallback_explicit(transcript: InterviewTranscript) -> str:
    lines: list[str] = []
    for r in transcript.rounds:
        if not r.answer or r.answer == "(no answer provided)":
            continue
        lines.append(f"- **{r.topic}:** {r.answer}")
    return "\n".join(lines) if lines else "_No explicit preferences captured._"


def _fallback_implicit(
    transcript: InterviewTranscript, seed_rules: list[Rule]
) -> str:
    hits: list[str] = []
    seen: set[str] = set()
    for r in transcript.rounds:
        for obs in r.implicit_observations:
            key = obs.strip()
            if key and key not in seen:
                hits.append(f"- _(from {r.topic})_ {key}")
                seen.add(key)
    if not hits and seed_rules:
        # Surface a handful of high-signal seed rules so the section isn't empty.
        for rule in seed_rules[:8]:
            hits.append(f"- _(seed: {rule.topic})_ {rule.statement}")
    return "\n".join(hits) if hits else "_No implicit patterns detected yet._"


def _fallback_formats(transcript: InterviewTranscript) -> str:
    for r in transcript.rounds:
        if r.question_id == "preferred_formats" and r.answer and r.answer != "(no answer provided)":
            return r.answer
    return "_Not specified — default to markdown._"


def _fallback_working(transcript: InterviewTranscript) -> str:
    parts: list[str] = []
    for r in transcript.rounds:
        if r.question_id in {"working_patterns", "feedback_style", "tools_environment"}:
            if r.answer and r.answer != "(no answer provided)":
                parts.append(f"- **{r.topic}:** {r.answer}")
    return "\n".join(parts) if parts else "_Not captured in interview._"


# ---------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------


def write_thinkprint(
    transcript: InterviewTranscript,
    seed_rules: list[Rule],
    out_path: Path,
    *,
    user_label: str = "Thinkprint",
    model: str = _DEFAULT_MODEL,
    api_key: str | None = None,
) -> Path:
    """Synthesize and write the final thinkprint.md to disk."""
    result = synthesize_profile(
        transcript, seed_rules, model=model, api_key=api_key
    )
    md = render_thinkprint_md(transcript, result, user_label=user_label)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    return out_path
