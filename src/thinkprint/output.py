"""Markdown rendering of a Thinkprint."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from thinkprint.models import Rule


def render_markdown(rules: list[Rule], title: str = "Thinkprint") -> str:
    """Group rules by topic, then by tier, and render to a single markdown doc."""
    if not rules:
        return f"# {title}\n\n_No rules extracted yet. Run `thinkprint extract` first._\n"

    by_topic: dict[str, list[Rule]] = defaultdict(list)
    for r in rules:
        by_topic[r.topic].append(r)

    lines: list[str] = [
        f"# {title}",
        "",
        f"_Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} · {len(rules)} rules across {len(by_topic)} topics_",
        "",
        "> **What this is:** behavioral rules extracted from your AI chat history and config files.",
        "> Tier 1 = explicit (from your CLAUDE.md, .cursorrules etc). Tier 2 = inferred from chat patterns.",
        "",
        "---",
        "",
    ]

    for topic in sorted(by_topic):
        topic_rules = sorted(by_topic[topic], key=lambda r: (r.tier, r.statement))
        lines.append(f"## {topic.replace('_', ' ').title()}")
        lines.append("")
        for r in topic_rules:
            lines.append(r.to_markdown())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
