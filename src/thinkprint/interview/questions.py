"""The Thinkprint interview question bank.

A Thinkprint is built through structured elicitation — not extraction.
Each round asks one focused question, optionally primed with an implicit
observation pulled from seed data (CLAUDE.md, prior chats, etc).

Six rounds, chosen to span the axes that actually change AI behavior:
identity, communication, formats, working patterns, feedback, tools.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


QuestionId = Literal[
    "identity_goals",
    "communication_style",
    "preferred_formats",
    "working_patterns",
    "feedback_style",
    "tools_environment",
]


class Question(BaseModel):
    """A single interview question.

    The question is immutable — the observation hint is attached later
    by the session runner after it looks at the seed data.
    """

    id: QuestionId
    topic: str
    prompt: str
    rationale: str = Field(
        ...,
        description="Why this question is in the bank — what axis of behavior it targets.",
    )
    followups: list[str] = Field(
        default_factory=list,
        description="Optional deeper probes if the answer is thin.",
    )


QUESTIONS: tuple[Question, ...] = (
    Question(
        id="identity_goals",
        topic="Identity & Goals",
        prompt=(
            "Who are you and what are you working on right now? "
            "In one paragraph: your role, what you're building, and the "
            "outcome you're chasing over the next 30–90 days."
        ),
        rationale=(
            "Anchors every other answer. Tone, format, and depth all shift "
            "based on whether someone is a founder shipping an MVP, a "
            "researcher writing a paper, or a designer making assets."
        ),
        followups=[
            "What distinguishes a good outcome from a great one for you?",
            "Who else is in the loop — solo, small team, or larger org?",
        ],
    ),
    Question(
        id="communication_style",
        topic="Communication Style",
        prompt=(
            "When an AI response feels right to you, what does it sound like? "
            "Walk me through: length, formality, whether it leads with the "
            "answer or the reasoning, bullets vs prose, any trailing summaries "
            "or sign-offs you hate."
        ),
        rationale=(
            "The #1 driver of friction in AI interactions. Getting this right "
            "once saves dozens of 'make it shorter' corrections later."
        ),
        followups=[
            "Give me an example of a response that felt just right.",
            "Any word or phrase you never want to see?",
        ],
    ),
    Question(
        id="preferred_formats",
        topic="Preferred Formats & Deliverables",
        prompt=(
            "What file formats do you most often want as the output? "
            "Markdown docs, Word files, PDFs, slide decks, code, spreadsheets, "
            "HTML artifacts, something else? When you ask for 'a writeup' or "
            "'a doc', what should I default to?"
        ),
        rationale=(
            "Format is where most AI work is wasted — the content is right, "
            "the container is wrong. Pinning defaults eliminates that."
        ),
        followups=[
            "Any formats you explicitly don't want?",
            "Where do finished files belong — a specific folder, a specific app?",
        ],
    ),
    Question(
        id="working_patterns",
        topic="Working Patterns",
        prompt=(
            "Walk me through a typical working session with an AI. Do you "
            "plan upfront or jump in? Do you want me to ask clarifying "
            "questions before starting, or take a best-guess pass and iterate?"
        ),
        rationale=(
            "Planning vs acting is a real axis of disagreement. Some users "
            "treat clarifying questions as helpful, others as stalling."
        ),
        followups=[
            "How big is the task you'd typically hand to an AI vs do yourself?",
            "Do you work in long sessions or short focused bursts?",
        ],
    ),
    Question(
        id="feedback_style",
        topic="Feedback & Correction",
        prompt=(
            "When I get something wrong, what's the fastest way to fix it? "
            "Do you prefer direct corrections, or do you want me to ask before "
            "changing course? How do you signal 'keep going' vs 'stop and reset'?"
        ),
        rationale=(
            "Writeback consent model starts here. Users vary enormously on how "
            "much they want an AI to self-correct vs defer."
        ),
        followups=[
            "When you say 'no', do you want me to propose alternatives or wait?",
            "Any failure mode you've seen repeatedly that drives you nuts?",
        ],
    ),
    Question(
        id="tools_environment",
        topic="Tools & Environment",
        prompt=(
            "What tools and platforms do you work in most? IDEs, apps, "
            "connectors (Slack, Notion, Gmail, GitHub, etc), operating system. "
            "Which integrations should I prioritize when I'm taking actions for you?"
        ),
        rationale=(
            "Connector priority. 'Prefer Linear over Jira' or 'I live in "
            "Notion not Google Docs' prevents a lot of wrong-tool output."
        ),
        followups=[
            "Any tool you're actively trying to move away from?",
            "What's your OS and main browser?",
        ],
    ),
)


def questions() -> tuple[Question, ...]:
    """Return the immutable question bank."""
    return QUESTIONS


def question_ids() -> tuple[str, ...]:
    """Return just the question IDs in order."""
    return tuple(q.id for q in QUESTIONS)
