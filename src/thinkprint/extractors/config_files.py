"""Tier 1 extraction: parse explicit config files into Rules with no LLM inference.

Sources:
- ~/.claude/CLAUDE.md (global)
- <project>/CLAUDE.md (project-level)
- ~/.claude/agents/*.md
- ~/.claude/commands/*.md
- .cursorrules / .windsurfrules / .zed/rules

These files are the user's explicit preference manifesto. For Claude Code power users this
tier alone produces 40-60% of the Thinkprint with zero inference cost.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from thinkprint.models import Evidence, Rule, RuleConfidence, Source

# Headings + bullets in CLAUDE.md often map directly to rule statements.
# We split on H2/H3 headings then keep bullets and short paragraphs as candidate rules.
_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.MULTILINE)
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$")


def _make_rule_id(source: Source, topic: str, statement: str) -> str:
    """Deterministic rule id so re-runs don't duplicate."""
    seed = f"{source.value}:{topic}:{statement}"
    return "tier1_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Return list of (section_title, section_body) pairs."""
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [("general", text)]

    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections.append((title, body))
    return sections


def _statements_from_section(body: str) -> list[str]:
    """Pull bullet items and short imperative lines out of a section body."""
    statements: list[str] = []
    for line in body.splitlines():
        bullet = _BULLET_RE.match(line)
        if bullet:
            text = bullet.group(1).strip()
            if 8 <= len(text) <= 280:
                statements.append(text)
            continue
        # Also pick up short standalone lines that read like rules
        stripped = line.strip()
        if (
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith("```")
            and 8 <= len(stripped) <= 280
            and any(stripped.lower().startswith(verb) for verb in _IMPERATIVE_VERBS)
        ):
            statements.append(stripped)
    return statements


_IMPERATIVE_VERBS = (
    "always",
    "never",
    "do not",
    "don't",
    "avoid",
    "prefer",
    "use",
    "ensure",
    "must",
    "should",
    "follow",
    "write",
    "keep",
    "make",
)


def _normalize_topic(title: str) -> str:
    """Convert section title into a slug-style topic."""
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug or "general"


def _extract_from_markdown(path: Path, source: Source) -> list[Rule]:
    """Generic markdown -> rule list. Used for CLAUDE.md, agent defs, command defs."""
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    rules: list[Rule] = []
    for title, body in _split_into_sections(text):
        topic = _normalize_topic(title)
        for stmt in _statements_from_section(body):
            rule_id = _make_rule_id(source, topic, stmt)
            evidence = Evidence(
                message_id=f"file:{path.name}",
                excerpt=stmt,
                source=source,
            )
            rules.append(
                Rule(
                    id=rule_id,
                    topic=topic,
                    statement=stmt,
                    tier=1,
                    confidence=RuleConfidence.HIGH,
                    evidence=[evidence],
                )
            )
    return rules


def _extract_from_plaintext(path: Path, source: Source, topic: str) -> list[Rule]:
    """Plain rule files like .cursorrules — one rule per non-empty line."""
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    rules: list[Rule] = []
    for line in text.splitlines():
        stmt = line.strip().lstrip("-*").strip()
        if 8 <= len(stmt) <= 280 and not stmt.startswith("#"):
            rule_id = _make_rule_id(source, topic, stmt)
            evidence = Evidence(
                message_id=f"file:{path.name}",
                excerpt=stmt,
                source=source,
            )
            rules.append(
                Rule(
                    id=rule_id,
                    topic=topic,
                    statement=stmt,
                    tier=1,
                    confidence=RuleConfidence.HIGH,
                    evidence=[evidence],
                )
            )
    return rules


def extract_config_rules(
    claude_dir: Path | None = None,
    project_dirs: list[Path] | None = None,
) -> list[Rule]:
    """Walk the user's Claude/Cursor/Windsurf config files and return Tier 1 rules.

    Args:
        claude_dir: Path to ~/.claude (or equivalent). If None, defaults to ~/.claude.
        project_dirs: Project roots to scan for project-level CLAUDE.md and IDE rule files.

    Returns:
        List of Rule objects, deduplicated by id.
    """
    rules: list[Rule] = []
    seen_ids: set[str] = set()

    def _add(new_rules: list[Rule]) -> None:
        for r in new_rules:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                rules.append(r)

    claude_dir = claude_dir or (Path.home() / ".claude")
    if claude_dir.is_dir():
        _add(_extract_from_markdown(claude_dir / "CLAUDE.md", Source.CLAUDE_MD))

        agents_dir = claude_dir / "agents"
        if agents_dir.is_dir():
            for f in sorted(agents_dir.glob("*.md")):
                _add(_extract_from_markdown(f, Source.CLAUDE_AGENT))

        commands_dir = claude_dir / "commands"
        if commands_dir.is_dir():
            for f in sorted(commands_dir.glob("*.md")):
                _add(_extract_from_markdown(f, Source.CLAUDE_COMMAND))

    for project in project_dirs or []:
        if not project.is_dir():
            continue
        _add(_extract_from_markdown(project / "CLAUDE.md", Source.CLAUDE_MD))
        _add(_extract_from_plaintext(project / ".cursorrules", Source.CURSOR_RULES, "cursor"))
        _add(_extract_from_plaintext(project / ".windsurfrules", Source.WINDSURF_RULES, "windsurf"))

    return rules
