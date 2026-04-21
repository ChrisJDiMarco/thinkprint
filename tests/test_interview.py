"""Tests for the interview module — question bank, batch runner, transcript IO."""

from __future__ import annotations

from pathlib import Path

import pytest

from thinkprint.interview import (
    InterviewRound,
    InterviewTranscript,
    derive_implicit_observations,
    load_answers,
    question_ids,
    questions,
    run_batch,
    save_transcript,
)
from thinkprint.models import Evidence, Rule, RuleConfidence, Source


def _rule(rid: str, topic: str, statement: str, tier: int = 1) -> Rule:
    return Rule(
        id=rid,
        topic=topic,
        statement=statement,
        tier=tier,
        confidence=RuleConfidence.HIGH,
        evidence=[Evidence(message_id="m1", excerpt="x", source=Source.CLAUDE_MD)],
    )


# ---------------------------------------------------------------------
# Question bank
# ---------------------------------------------------------------------


def test_question_bank_has_six_rounds():
    # Arrange / Act
    bank = questions()

    # Assert — the product spec requires at least 5 rounds; we ship 6.
    assert len(bank) == 6


def test_question_bank_covers_all_expected_axes():
    # Arrange
    expected = {
        "identity_goals",
        "communication_style",
        "preferred_formats",
        "working_patterns",
        "feedback_style",
        "tools_environment",
    }

    # Act
    ids = set(question_ids())

    # Assert
    assert ids == expected


def test_each_question_has_prompt_and_rationale():
    for q in questions():
        assert q.prompt.strip(), f"{q.id} missing prompt"
        assert q.rationale.strip(), f"{q.id} missing rationale"
        assert q.topic.strip(), f"{q.id} missing topic"


def test_question_ids_are_stable_order():
    # Running twice returns the exact same tuple — no hidden state.
    assert question_ids() == question_ids()


# ---------------------------------------------------------------------
# derive_implicit_observations
# ---------------------------------------------------------------------


def test_implicit_observations_match_on_topic_keywords():
    # Arrange
    seeds = [
        _rule("r1", "communication", "Be terse and lead with the answer"),
        _rule("r2", "tools", "Use Notion as primary doc store"),
        _rule("r3", "random", "Something unrelated"),
    ]
    comm_q = next(q for q in questions() if q.id == "communication_style")
    tools_q = next(q for q in questions() if q.id == "tools_environment")

    # Act
    comm_hits = derive_implicit_observations(comm_q, seeds)
    tools_hits = derive_implicit_observations(tools_q, seeds)

    # Assert
    assert any("terse" in h.lower() for h in comm_hits)
    assert any("notion" in h.lower() for h in tools_hits)


def test_implicit_observations_returns_empty_when_no_match():
    # Arrange
    seeds = [_rule("r1", "unrelated", "Totally off-topic content")]
    identity_q = next(q for q in questions() if q.id == "identity_goals")

    # Act
    hits = derive_implicit_observations(identity_q, seeds)

    # Assert
    assert hits == []


def test_implicit_observations_deduplicate():
    # Arrange — same statement twice should surface once.
    seeds = [
        _rule("r1", "communication", "Be terse"),
        _rule("r2", "communication", "Be terse"),
    ]
    q = next(q for q in questions() if q.id == "communication_style")

    # Act
    hits = derive_implicit_observations(q, seeds)

    # Assert
    assert hits.count("Be terse") == 1


def test_implicit_observations_capped_at_five():
    # Arrange — more than 5 matches should cap.
    seeds = [
        _rule(f"r{i}", "tools", f"Use Notion variant {i}") for i in range(10)
    ]
    q = next(q for q in questions() if q.id == "tools_environment")

    # Act
    hits = derive_implicit_observations(q, seeds)

    # Assert
    assert len(hits) <= 5


# ---------------------------------------------------------------------
# Transcript model (immutability)
# ---------------------------------------------------------------------


def test_transcript_append_is_immutable():
    # Arrange
    t = InterviewTranscript()
    r = InterviewRound(
        question_id="identity_goals",
        topic="Identity",
        prompt="who?",
        answer="me",
    )

    # Act
    t2 = t.append(r)

    # Assert — original is untouched, new one has the round.
    assert len(t.rounds) == 0
    assert len(t2.rounds) == 1
    assert t is not t2


def test_transcript_finalize_stamps_finish_time():
    # Arrange
    t = InterviewTranscript()

    # Act
    t2 = t.finalize()

    # Assert
    assert t.finished_at is None
    assert t2.finished_at is not None


# ---------------------------------------------------------------------
# run_batch
# ---------------------------------------------------------------------


def test_run_batch_produces_one_round_per_question():
    # Arrange
    answers = {qid: f"answer for {qid}" for qid in question_ids()}

    # Act
    transcript = run_batch(answers, seed_rules=[])

    # Assert
    assert len(transcript.rounds) == len(question_ids())
    assert [r.question_id for r in transcript.rounds] == list(question_ids())


def test_run_batch_records_answers_verbatim():
    # Arrange
    answers = {"identity_goals": "I am Chris", "communication_style": "Be terse"}

    # Act
    transcript = run_batch(answers, seed_rules=[])

    # Assert
    id_round = next(r for r in transcript.rounds if r.question_id == "identity_goals")
    assert id_round.answer == "I am Chris"


def test_run_batch_marks_missing_answers():
    # Arrange — no answers provided.
    # Act
    transcript = run_batch({}, seed_rules=[])

    # Assert — every round gets a placeholder, never a silent empty.
    for r in transcript.rounds:
        assert r.answer == "(no answer provided)"


def test_run_batch_attaches_implicit_observations():
    # Arrange
    seeds = [_rule("r1", "communication", "Be terse and direct")]
    answers = {qid: "x" for qid in question_ids()}

    # Act
    transcript = run_batch(answers, seed_rules=seeds)

    # Assert — the communication round should have observations attached.
    comm = next(r for r in transcript.rounds if r.question_id == "communication_style")
    assert comm.implicit_observations
    assert any("terse" in obs.lower() for obs in comm.implicit_observations)


def test_run_batch_tracks_seed_rule_count():
    # Arrange
    seeds = [_rule(f"r{i}", "topic", f"s{i}") for i in range(7)]

    # Act
    transcript = run_batch({}, seed_rules=seeds)

    # Assert
    assert transcript.seed_rule_count == 7


def test_run_batch_finalizes_transcript():
    # Act
    transcript = run_batch({}, seed_rules=[])

    # Assert — batch is a complete run, so finished_at is stamped.
    assert transcript.finished_at is not None


# ---------------------------------------------------------------------
# load_answers / save_transcript (JSON round-trip)
# ---------------------------------------------------------------------


def test_load_answers_roundtrip(tmp_path: Path):
    # Arrange
    import json

    p = tmp_path / "answers.json"
    payload = {"identity_goals": "a", "communication_style": "b"}
    p.write_text(json.dumps(payload), encoding="utf-8")

    # Act
    loaded = load_answers(p)

    # Assert
    assert loaded == payload


def test_load_answers_rejects_non_object(tmp_path: Path):
    # Arrange
    p = tmp_path / "bad.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")

    # Act / Assert
    with pytest.raises(ValueError):
        load_answers(p)


def test_save_transcript_writes_valid_json(tmp_path: Path):
    # Arrange
    import json

    answers = {qid: "x" for qid in question_ids()}
    transcript = run_batch(answers, seed_rules=[])
    out = tmp_path / ".thinkprint" / "interview.json"

    # Act
    save_transcript(transcript, out)

    # Assert
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "rounds" in data
    assert len(data["rounds"]) == len(question_ids())
