"""Interview session — runs the Q&A loop.

Two modes:
- Interactive: prompts the user one question at a time via click.prompt.
- Batch: reads answers from a JSON file keyed by question id.

Both produce the same InterviewTranscript, which is the input to the
profile synthesizer. Seed observations (implicit hints pulled from the
user's configs and chat history) are attached per-round so the
synthesizer can distinguish "user said this" from "we inferred this".
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, TextIO

import click
from pydantic import BaseModel, Field

from ..models import Rule
from .questions import Question, questions


class InterviewRound(BaseModel):
    """One question and the answer captured for it."""

    question_id: str
    topic: str
    prompt: str
    answer: str
    implicit_observations: list[str] = Field(default_factory=list)
    followups_asked: list[str] = Field(default_factory=list)


class InterviewTranscript(BaseModel):
    """Full interview result — ordered rounds plus seed context."""

    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    rounds: list[InterviewRound] = Field(default_factory=list)
    seed_rule_count: int = 0

    def append(self, round_: InterviewRound) -> "InterviewTranscript":
        """Return a new transcript with the round appended (immutable)."""
        return InterviewTranscript(
            started_at=self.started_at,
            finished_at=self.finished_at,
            rounds=[*self.rounds, round_],
            seed_rule_count=self.seed_rule_count,
        )

    def finalize(self) -> "InterviewTranscript":
        """Return a new transcript stamped with a finish time."""
        return InterviewTranscript(
            started_at=self.started_at,
            finished_at=datetime.utcnow(),
            rounds=self.rounds,
            seed_rule_count=self.seed_rule_count,
        )


def derive_implicit_observations(
    question: Question, seed_rules: Iterable[Rule]
) -> list[str]:
    """Pick implicit hints from seed rules that are relevant to a question.

    Pure substring match on topic keywords — deliberately simple. The
    synthesizer handles real fusion later. This is only a prompt-prime.
    """
    keywords = _KEYWORDS_BY_QUESTION.get(question.id, ())
    if not keywords:
        return []

    hits: list[str] = []
    seen: set[str] = set()
    for rule in seed_rules:
        text = rule.statement.lower()
        topic = rule.topic.lower()
        if any(k in text or k in topic for k in keywords):
            key = rule.statement.strip()
            if key and key not in seen:
                hits.append(key)
                seen.add(key)
        if len(hits) >= 5:
            break
    return hits


_KEYWORDS_BY_QUESTION: dict[str, tuple[str, ...]] = {
    "identity_goals": ("role", "goal", "founder", "builder", "business"),
    "communication_style": (
        "terse",
        "concise",
        "prose",
        "bullet",
        "summary",
        "lead with",
        "tone",
    ),
    "preferred_formats": (
        "markdown",
        "docx",
        "pdf",
        "html",
        "format",
        "file",
        "artifact",
    ),
    "working_patterns": (
        "plan",
        "planning",
        "clarif",
        "iterate",
        "session",
        "scope",
    ),
    "feedback_style": (
        "correction",
        "feedback",
        "fix",
        "undo",
        "never",
        "do not",
        "stop",
    ),
    "tools_environment": (
        "notion",
        "slack",
        "github",
        "gmail",
        "mcp",
        "tool",
        "integration",
    ),
}


def run_interactive(
    seed_rules: list[Rule],
    out: TextIO | None = None,
) -> InterviewTranscript:
    """Run the interview interactively via click.prompt."""
    echo = _make_echo(out)
    transcript = InterviewTranscript(seed_rule_count=len(seed_rules))

    echo("Thinkprint interview — 6 rounds, answer as long as you want.")
    echo("Type your answer and press enter twice to finish each round.\n")

    for i, q in enumerate(questions(), start=1):
        implicit = derive_implicit_observations(q, seed_rules)
        echo(f"--- Round {i}/6 · {q.topic} ---")
        echo(q.prompt)
        if implicit:
            echo("\nI noticed this from your existing configs:")
            for obs in implicit:
                echo(f"  · {obs[:180]}")
            echo("\nFeel free to confirm, correct, or ignore any of it.\n")
        answer = _multiline_prompt()
        transcript = transcript.append(
            InterviewRound(
                question_id=q.id,
                topic=q.topic,
                prompt=q.prompt,
                answer=answer.strip(),
                implicit_observations=implicit,
            )
        )
        echo("")

    return transcript.finalize()


def run_batch(
    answers: dict[str, str],
    seed_rules: list[Rule],
) -> InterviewTranscript:
    """Run the interview against a pre-filled answers dict.

    Useful for tests, CI, and users who want to answer in their editor
    rather than a CLI prompt. Unknown question ids are ignored; missing
    ids get an empty answer and a note.
    """
    transcript = InterviewTranscript(seed_rule_count=len(seed_rules))
    for q in questions():
        implicit = derive_implicit_observations(q, seed_rules)
        answer = answers.get(q.id, "").strip()
        transcript = transcript.append(
            InterviewRound(
                question_id=q.id,
                topic=q.topic,
                prompt=q.prompt,
                answer=answer or "(no answer provided)",
                implicit_observations=implicit,
            )
        )
    return transcript.finalize()


def load_answers(path: Path) -> dict[str, str]:
    """Read an answers JSON file: {question_id: answer_text}."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"answers file must be a JSON object, got {type(data).__name__}")
    return {str(k): str(v) for k, v in data.items()}


def save_transcript(transcript: InterviewTranscript, path: Path) -> None:
    """Persist a transcript to disk as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(transcript.model_dump_json(indent=2))


def _make_echo(out: TextIO | None):
    def echo(msg: str) -> None:
        if out is None:
            click.echo(msg)
        else:
            out.write(msg + "\n")

    return echo


def _multiline_prompt() -> str:
    """Read a multi-line answer until an empty line is entered."""
    click.echo("> ", nl=False)
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip() and lines:
            break
        lines.append(line)
    return "\n".join(lines)
