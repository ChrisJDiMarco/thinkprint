"""Tests for config + chat-export extractors."""

from __future__ import annotations

from thinkprint.extractors import (
    extract_config_rules,
    parse_chatgpt_export,
    parse_claude_export,
)
from thinkprint.models import Role, Source


def test_extract_config_rules_from_claude_dir(fake_claude_dir):
    rules = extract_config_rules(claude_dir=fake_claude_dir)
    assert rules, "should extract at least some rules from CLAUDE.md + agents + commands"
    statements = [r.statement for r in rules]
    assert any("immutable" in s.lower() for s in statements)
    assert any("parameterized" in s.lower() for s in statements)
    assert any("tests before shipping" in s.lower() for s in statements)
    # All Tier 1
    assert all(r.tier == 1 for r in rules)
    # Source diversity
    sources = {r.evidence[0].source for r in rules if r.evidence}
    assert Source.CLAUDE_MD in sources
    assert Source.CLAUDE_AGENT in sources
    assert Source.CLAUDE_COMMAND in sources


def test_extract_config_rules_from_project_dirs(fake_project_dir):
    rules = extract_config_rules(claude_dir=None, project_dirs=[fake_project_dir])
    statements = [r.statement.lower() for r in rules]
    assert any("ruff" in s for s in statements)
    assert any("typescript strict" in s for s in statements)


def test_extract_config_rules_dedupes_across_runs(fake_claude_dir):
    rules1 = extract_config_rules(claude_dir=fake_claude_dir)
    rules2 = extract_config_rules(claude_dir=fake_claude_dir)
    ids1 = {r.id for r in rules1}
    ids2 = {r.id for r in rules2}
    assert ids1 == ids2, "rule ids must be deterministic across runs"


def test_extract_config_rules_handles_missing_dir(tmp_path):
    rules = extract_config_rules(claude_dir=tmp_path / "nope", project_dirs=[])
    assert rules == []


def test_parse_chatgpt_export(chatgpt_export_path):
    msgs = parse_chatgpt_export(chatgpt_export_path)
    assert len(msgs) == 8  # 5 from conv1 + 3 from conv2
    assert all(m.source == Source.CHATGPT_EXPORT for m in msgs)
    assert {m.role for m in msgs} == {Role.USER, Role.ASSISTANT}
    # Conversation grouping preserved
    assert len({m.conversation_id for m in msgs}) == 2


def test_parse_chatgpt_export_handles_garbage(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("not json", encoding="utf-8")
    assert parse_chatgpt_export(p) == []


def test_parse_claude_export(claude_export_path):
    msgs = parse_claude_export(claude_export_path)
    assert len(msgs) == 5
    assert all(m.source == Source.CLAUDE_EXPORT for m in msgs)
    assert {m.role for m in msgs} == {Role.USER, Role.ASSISTANT}
