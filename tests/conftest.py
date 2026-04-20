"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from thinkprint.models import Message, Role, Source


@pytest.fixture
def claude_md_text() -> str:
    return """# My Coding Style

## Principles
- Always prefer immutable data structures
- Never use bullet points in casual responses
- Avoid emojis unless asked

## Communication
- Be terse — no trailing summaries
- Lead with the answer, not reasoning
"""


@pytest.fixture
def fake_claude_dir(tmp_path: Path, claude_md_text: str) -> Path:
    """A populated ~/.claude-style directory we can point extractors at."""
    base = tmp_path / "claude_home"
    (base / "agents").mkdir(parents=True)
    (base / "commands").mkdir(parents=True)
    (base / "CLAUDE.md").write_text(claude_md_text, encoding="utf-8")
    (base / "agents" / "reviewer.md").write_text(
        "# Reviewer Agent\n\n- Always check for SQL injection\n- Prefer parameterized queries\n",
        encoding="utf-8",
    )
    (base / "commands" / "ship.md").write_text(
        "# Ship Command\n\n- Run tests before shipping\n- Never push to main directly\n",
        encoding="utf-8",
    )
    return base


@pytest.fixture
def fake_project_dir(tmp_path: Path) -> Path:
    base = tmp_path / "myproj"
    base.mkdir()
    (base / "CLAUDE.md").write_text(
        "# Project Style\n\n- Use ruff for linting\n- Keep files under 800 lines\n",
        encoding="utf-8",
    )
    (base / ".cursorrules").write_text(
        "Use TypeScript strict mode\nPrefer functional components\n", encoding="utf-8"
    )
    return base


@pytest.fixture
def chatgpt_export_path(tmp_path: Path) -> Path:
    """Build a minimal ChatGPT export with two conversations and a few turns."""
    data = [
        {
            "id": "conv1",
            "mapping": {
                "n1": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["How should I structure a Python project?"]},
                        "create_time": 1700000000,
                    }
                },
                "n2": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["Here's a long detailed structure with src/ layout..."]},
                        "create_time": 1700000010,
                    }
                },
                "n3": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["Make it shorter, just the key points please"]},
                        "create_time": 1700000020,
                    }
                },
                "n4": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["src/, tests/, pyproject.toml. Done."]},
                        "create_time": 1700000030,
                    }
                },
                "n5": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["Perfect, that's exactly what I needed"]},
                        "create_time": 1700000040,
                    }
                },
            },
        },
        {
            "id": "conv2",
            "mapping": {
                "m1": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["Review this auth code for security issues"]},
                    }
                },
                "m2": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["I'd suggest using bcrypt for password hashing..."]},
                    }
                },
                "m3": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["Be more concise, I just want the top 3 issues"]},
                    }
                },
            },
        },
    ]
    p = tmp_path / "chatgpt_export.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.fixture
def claude_export_path(tmp_path: Path) -> Path:
    data = [
        {
            "uuid": "claude-conv-1",
            "chat_messages": [
                {"uuid": "1", "sender": "human", "text": "Help me write a postmortem for this incident"},
                {"uuid": "2", "sender": "assistant", "text": "Sure, what happened?"},
                {"uuid": "3", "sender": "human", "text": "The deploy failed at 2am, took 4 hours to fix"},
                {"uuid": "4", "sender": "assistant", "text": "Here's a structured postmortem template..."},
                {"uuid": "5", "sender": "human", "text": "Nailed it, ship it"},
            ],
        }
    ]
    p = tmp_path / "claude_export.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.fixture
def sample_messages() -> list[Message]:
    return [
        Message(
            id="m1",
            conversation_id="c1",
            role=Role.USER,
            content="How do I implement OAuth in Python?",
            source=Source.CHATGPT_EXPORT,
        ),
        Message(
            id="m2",
            conversation_id="c1",
            role=Role.ASSISTANT,
            content="Here is a detailed walkthrough using authlib...",
            source=Source.CHATGPT_EXPORT,
        ),
        Message(
            id="m3",
            conversation_id="c1",
            role=Role.USER,
            content="Make it shorter please",
            source=Source.CHATGPT_EXPORT,
        ),
        Message(
            id="m4",
            conversation_id="c1",
            role=Role.ASSISTANT,
            content="Use authlib. pip install authlib. Done.",
            source=Source.CHATGPT_EXPORT,
        ),
        Message(
            id="m5",
            conversation_id="c1",
            role=Role.USER,
            content="Perfect, exactly what I wanted",
            source=Source.CHATGPT_EXPORT,
        ),
    ]
