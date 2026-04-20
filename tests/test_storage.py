"""Round-trip tests for SQLite storage."""

from __future__ import annotations

from pathlib import Path

from thinkprint.models import Evidence, Rule, RuleConfidence, Source
from thinkprint.storage import list_topics, load_rules, save_rules


def _rule(rid: str, topic: str, statement: str, tier: int = 1) -> Rule:
    return Rule(
        id=rid,
        topic=topic,
        statement=statement,
        tier=tier,
        confidence=RuleConfidence.HIGH,
        evidence=[
            Evidence(message_id="msg1", excerpt="example", source=Source.CLAUDE_MD)
        ],
    )


def test_save_and_load(tmp_path: Path):
    db = tmp_path / "tp.db"
    rules_in = [
        _rule("r1", "writing", "Be terse"),
        _rule("r2", "code_review", "Always check for SQLi"),
    ]
    save_rules(db, rules_in)
    rules_out = load_rules(db)
    assert {r.id for r in rules_out} == {"r1", "r2"}
    assert all(r.evidence for r in rules_out)


def test_load_filtered_by_topic(tmp_path: Path):
    db = tmp_path / "tp.db"
    save_rules(
        db,
        [
            _rule("r1", "writing", "Be terse"),
            _rule("r2", "code_review", "Check SQLi"),
            _rule("r3", "writing_prose", "Avoid bullets"),
        ],
    )
    rules = load_rules(db, topic="writing")
    assert {r.id for r in rules} == {"r1", "r3"}


def test_list_topics(tmp_path: Path):
    db = tmp_path / "tp.db"
    save_rules(
        db,
        [
            _rule("r1", "writing", "a"),
            _rule("r2", "writing", "b"),
            _rule("r3", "code", "c"),
        ],
    )
    topics = dict(list_topics(db))
    assert topics == {"writing": 2, "code": 1}


def test_replace_wipes_prior(tmp_path: Path):
    db = tmp_path / "tp.db"
    save_rules(db, [_rule("r1", "x", "a")])
    save_rules(db, [_rule("r2", "y", "b")], replace=True)
    rules = load_rules(db)
    assert {r.id for r in rules} == {"r2"}
