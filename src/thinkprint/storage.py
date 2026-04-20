"""SQLite storage for rules + evidence.

Schema is intentionally simple: rules + evidence tables, with topic + tier indexed.
Every persistence helper is idempotent — re-running extract should overwrite cleanly.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from thinkprint.models import Evidence, Rule, RuleConfidence, Source

_SCHEMA = """
CREATE TABLE IF NOT EXISTS rules (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    statement TEXT NOT NULL,
    tier INTEGER NOT NULL,
    confidence TEXT NOT NULL,
    source_cluster_id INTEGER,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rules_topic ON rules(topic);
CREATE INDEX IF NOT EXISTS idx_rules_tier ON rules(tier);

CREATE TABLE IF NOT EXISTS evidence (
    rule_id TEXT NOT NULL,
    ord INTEGER NOT NULL,
    message_id TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (rule_id, ord),
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE
);
"""


@contextmanager
def _connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    """Create the schema if it doesn't exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def save_rules(db_path: Path, rules: list[Rule], replace: bool = True) -> None:
    """Persist rules to SQLite. If replace=True, wipes prior state first."""
    init_db(db_path)
    with _connect(db_path) as conn:
        if replace:
            conn.execute("DELETE FROM evidence")
            conn.execute("DELETE FROM rules")
        for r in rules:
            conn.execute(
                "INSERT OR REPLACE INTO rules(id, topic, statement, tier, confidence, source_cluster_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    r.id,
                    r.topic,
                    r.statement,
                    r.tier,
                    r.confidence.value,
                    r.source_cluster_id,
                    r.created_at.isoformat(),
                ),
            )
            for i, ev in enumerate(r.evidence):
                conn.execute(
                    "INSERT OR REPLACE INTO evidence(rule_id, ord, message_id, excerpt, source) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (r.id, i, ev.message_id, ev.excerpt, ev.source.value),
                )


def _row_to_rule(row: sqlite3.Row, evidence: list[Evidence]) -> Rule:
    return Rule(
        id=row["id"],
        topic=row["topic"],
        statement=row["statement"],
        tier=row["tier"],
        confidence=RuleConfidence(row["confidence"]),
        source_cluster_id=row["source_cluster_id"],
        evidence=evidence,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def load_rules(db_path: Path, topic: str | None = None, limit: int | None = None) -> list[Rule]:
    """Load rules from disk, optionally filtered by topic and capped by limit."""
    if not db_path.is_file():
        return []
    with _connect(db_path) as conn:
        query = "SELECT * FROM rules"
        params: tuple = ()
        if topic:
            query += " WHERE topic LIKE ?"
            params = (f"%{topic}%",)
        query += " ORDER BY tier ASC, confidence DESC, created_at DESC"
        if limit:
            query += f" LIMIT {int(limit)}"

        rule_rows = conn.execute(query, params).fetchall()

        rules: list[Rule] = []
        for r in rule_rows:
            ev_rows = conn.execute(
                "SELECT * FROM evidence WHERE rule_id = ? ORDER BY ord ASC", (r["id"],)
            ).fetchall()
            evidence = [
                Evidence(
                    message_id=ev["message_id"],
                    excerpt=ev["excerpt"],
                    source=Source(ev["source"]),
                )
                for ev in ev_rows
            ]
            rules.append(_row_to_rule(r, evidence))
        return rules


def list_topics(db_path: Path) -> list[tuple[str, int]]:
    """Return (topic, rule_count) pairs."""
    if not db_path.is_file():
        return []
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT topic, COUNT(*) AS n FROM rules GROUP BY topic ORDER BY n DESC"
        ).fetchall()
        return [(r["topic"], r["n"]) for r in rows]


def export_json(db_path: Path) -> str:
    """Dump the entire DB as JSON for portability."""
    rules = load_rules(db_path)
    return json.dumps(
        [r.model_dump(mode="json") for r in rules],
        indent=2,
        default=str,
    )
