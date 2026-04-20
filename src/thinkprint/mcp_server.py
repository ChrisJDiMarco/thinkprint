"""MCP server exposing the Thinkprint to any compliant AI client.

Built on the official `mcp` Python SDK (FastMCP). One connection, three primitives:

Resource:  thinkprint://rules/all       — full markdown profile
Tool:      get_rules(topic, limit)      — filter rules by topic
Tool:      list_topics()                — discover what topics exist

Run:  thinkprint serve --db ./.thinkprint/thinkprint.db

Then in Claude Desktop / Claude Code config, add a stdio MCP server entry pointing at:
  command: thinkprint
  args:    ["serve", "--db", "/abs/path/to/.thinkprint/thinkprint.db"]
"""

from __future__ import annotations

import json
from pathlib import Path

from thinkprint.output import render_markdown
from thinkprint.storage import list_topics, load_rules


def build_server(db_path: Path):
    """Construct a FastMCP server bound to the given Thinkprint DB.

    Imported lazily so the rest of the package works without `mcp` installed.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "mcp package not installed. Install with: pip install mcp"
        ) from exc

    server = FastMCP("thinkprint")

    @server.resource("thinkprint://rules/all")
    def all_rules_md() -> str:
        """Return the full Thinkprint as markdown."""
        rules = load_rules(db_path)
        return render_markdown(rules, title="Thinkprint")

    @server.tool()
    def get_rules(topic: str = "", limit: int = 10) -> str:
        """Return behavioral rules matching a topic (substring match). Empty topic = all.

        Args:
            topic: keyword/topic to filter by (e.g. "code review", "writing")
            limit: max rules to return (default 10)
        """
        rules = load_rules(db_path, topic=topic or None, limit=limit)
        if not rules:
            return f"No rules found for topic={topic!r}."
        payload = [
            {
                "topic": r.topic,
                "statement": r.statement,
                "tier": r.tier,
                "confidence": r.confidence.value,
                "evidence_count": len(r.evidence),
            }
            for r in rules
        ]
        return json.dumps(payload, indent=2)

    @server.tool()
    def list_thinkprint_topics() -> str:
        """List all topics in the user's Thinkprint with rule counts."""
        topics = list_topics(db_path)
        if not topics:
            return "No topics yet. Run `thinkprint extract` first."
        return json.dumps(
            [{"topic": t, "rule_count": n} for t, n in topics],
            indent=2,
        )

    return server


def run_server(db_path: Path) -> None:
    """Block on the MCP server's stdio loop."""
    server = build_server(db_path)
    server.run()
