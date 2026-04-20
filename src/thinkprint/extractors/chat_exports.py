"""Tier 2 extraction: parse ChatGPT and Claude conversation exports into Messages.

ChatGPT export format (conversations.json) — a list of conversation dicts where each
has a `mapping` of node_id -> {message: {author: {role}, content: {parts: [...]}}}.

Claude export format — a list of conversation dicts each with a `chat_messages` array
of {sender: "human"|"assistant", text: "..."} entries.

Both formats vary by year. We tolerate missing fields and skip anything malformed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from thinkprint.models import Message, Role, Source


def _stable_id(*parts: str) -> str:
    seed = "|".join(parts)
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _coerce_role(raw: str | None) -> Role | None:
    if not raw:
        return None
    raw = raw.lower().strip()
    if raw in ("user", "human"):
        return Role.USER
    if raw in ("assistant", "ai"):
        return Role.ASSISTANT
    if raw == "system":
        return Role.SYSTEM
    return None


def _ts_to_dt(ts: Any) -> datetime | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _content_to_text(content: Any) -> str:
    """ChatGPT messages have `content.parts: [str | dict, ...]` — flatten to a string."""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        parts = content.get("parts") or []
        chunks: list[str] = []
        for p in parts:
            if isinstance(p, str):
                chunks.append(p)
            elif isinstance(p, dict):
                # multimodal turns sometimes contain dict parts; pull text if present
                if "text" in p and isinstance(p["text"], str):
                    chunks.append(p["text"])
        return "\n".join(c for c in chunks if c)
    return ""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def parse_chatgpt_export(path: Path) -> list[Message]:
    """Parse a ChatGPT conversations.json export into normalized Messages."""
    data = _load_json(path)
    if not isinstance(data, list):
        return []

    messages: list[Message] = []
    for conv in data:
        if not isinstance(conv, dict):
            continue
        conv_id = str(conv.get("id") or conv.get("conversation_id") or _stable_id(json.dumps(conv)[:64]))
        mapping = conv.get("mapping") or {}
        if not isinstance(mapping, dict):
            continue

        for node_id, node in mapping.items():
            if not isinstance(node, dict):
                continue
            msg = node.get("message")
            if not isinstance(msg, dict):
                continue
            role = _coerce_role((msg.get("author") or {}).get("role"))
            if role is None:
                continue
            text = _content_to_text(msg.get("content"))
            if not text or not text.strip():
                continue
            messages.append(
                Message(
                    id=_stable_id(conv_id, str(node_id)),
                    conversation_id=conv_id,
                    role=role,
                    content=text,
                    created_at=_ts_to_dt(msg.get("create_time")),
                    source=Source.CHATGPT_EXPORT,
                )
            )
    return messages


def parse_claude_export(path: Path) -> list[Message]:
    """Parse a Claude conversation export into normalized Messages.

    Tolerates both the array-of-conversations form and a single-conversation dict.
    """
    data = _load_json(path)
    if data is None:
        return []
    convs = data if isinstance(data, list) else [data]

    messages: list[Message] = []
    for conv in convs:
        if not isinstance(conv, dict):
            continue
        conv_id = str(conv.get("uuid") or conv.get("id") or _stable_id(json.dumps(conv)[:64]))
        chat_messages: Iterable[Any] = conv.get("chat_messages") or conv.get("messages") or []

        for i, m in enumerate(chat_messages):
            if not isinstance(m, dict):
                continue
            role = _coerce_role(m.get("sender") or m.get("role"))
            if role is None:
                continue
            text = m.get("text")
            if text is None:
                # Anthropic export sometimes uses "content" with parts
                text = _content_to_text(m.get("content"))
            if not isinstance(text, str) or not text.strip():
                continue
            messages.append(
                Message(
                    id=_stable_id(conv_id, str(m.get("uuid") or i)),
                    conversation_id=conv_id,
                    role=role,
                    content=text,
                    created_at=_ts_to_dt(m.get("created_at")),
                    source=Source.CLAUDE_EXPORT,
                )
            )
    return messages
