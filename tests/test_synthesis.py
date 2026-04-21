"""Tests for the synthesis module — template fallback path + markdown render.

LLM path is skipped: it requires an API key and network. The fallback path
is the one we need green every commit.
"""

from __future__ import annotations

from pathlib import Path

from thinkprint.interview import question_ids, run_batch
from thinkprint.models import Evidence, Rule, RuleConfidence, Source
from thinkprint.synthesis import (
    SynthesisResult,
    render_thinkprint_md,
    synthesize_profile,
    write_thinkprint,
)
from thinkprint.synthesis.profile import _rank_seed_rules


def _rule(rid: str, topic: str, statement: str, tier: int = 1) -> Rule:
    return Rule(
        id=rid,
        topic=topic,
        statement=statement,
        tier=tier,
        confidence=RuleConfidence.HIGH,
        evidence=[Evidence(message_id="m1", excerpt="x", source=Source.CLAUDE_MD)],
    )


def _full_answers() -> dict[str, str]:
    return {
        "identity_goals": "I'm a solo founder shipping an AI product in the next 60 days.",
        "communication_style": "Terse. Lead with the answer. No trailing summaries.",
        "preferred_formats": "Markdown for docs, HTML artifacts for anything visual.",
        "working_patterns": "Best-guess first pass, iterate. Don't ask 5 questions before starting.",
        "feedback_style": "Direct corrections, no softening. Stop when I say stop.",
        "tools_environment": "macOS, Notion, Slack, GitHub, Gmail. Prefer direct MCPs over Chrome.",
    }


# ---------------------------------------------------------------------
# synthesize_profile — fallback path
# ---------------------------------------------------------------------


def test_synthesize_fallback_when_no_api_key(monkeypatch):
    # Arrange — ensure no API key is visible.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])

    # Act
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Assert
    assert isinstance(result, SynthesisResult)
    assert result.used_llm is False


def test_fallback_identity_uses_identity_answer(monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    answers = _full_answers()
    transcript = run_batch(answers, seed_rules=[])

    # Act
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Assert — the identity section should carry the user's stated identity.
    assert "solo founder" in result.identity


def test_fallback_explicit_covers_all_answered_rounds(monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])

    # Act
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Assert — every round title should appear in explicit preferences.
    for r in transcript.rounds:
        assert r.topic in result.explicit_preferences


def test_fallback_implicit_falls_back_to_seed_rules_when_no_observations(monkeypatch):
    # Arrange — answers unrelated to any seed topic keyword ensures no
    # implicit observations get attached during interview, forcing the
    # synthesizer to surface seed rules directly.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch({qid: "x" for qid in question_ids()}, seed_rules=[])
    seeds = [_rule("r1", "obscure_topic", "A very specific seed statement")]

    # Act
    result = synthesize_profile(transcript, seed_rules=seeds, api_key=None)

    # Assert
    assert "A very specific seed statement" in result.implicit_patterns


def test_fallback_implicit_prefers_observations_over_seeds(monkeypatch):
    # Arrange — seed rule matches a topic keyword, so interview attaches it
    # as an implicit observation. Synthesis should surface that observation
    # (not the raw seed-rule fallback section).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    seeds = [_rule("r1", "communication", "Be terse and direct")]
    transcript = run_batch(_full_answers(), seed_rules=seeds)

    # Act
    result = synthesize_profile(transcript, seed_rules=seeds, api_key=None)

    # Assert — observation is tagged with its round, not with "seed:".
    assert "Be terse and direct" in result.implicit_patterns
    assert "(from Communication Style)" in result.implicit_patterns


def test_fallback_formats_uses_formats_answer(monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])

    # Act
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Assert
    assert "Markdown" in result.preferred_formats


def test_fallback_working_style_combines_three_rounds(monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])

    # Act
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Assert — working_style should pull from working_patterns, feedback_style,
    # and tools_environment rounds.
    assert "Working Patterns" in result.working_style
    assert "Feedback & Correction" in result.working_style
    assert "Tools & Environment" in result.working_style


# ---------------------------------------------------------------------
# render_thinkprint_md
# ---------------------------------------------------------------------


def test_render_markdown_contains_all_seven_sections(monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Act
    md = render_thinkprint_md(transcript, result, user_label="Test User")

    # Assert
    assert "# Test User" in md
    assert "## 1. Identity" in md
    assert "## 2. Explicit preferences" in md
    assert "## 3. Implicit patterns" in md
    assert "## 4. Preferred formats" in md
    assert "## 5. Working style" in md
    assert "## 6. Contradictions" in md
    assert "## 7. Interview transcript" in md


def test_render_markdown_flags_template_fallback(monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Act
    md = render_thinkprint_md(transcript, result)

    # Assert — fallback path should carry a note telling the user to set their key.
    assert "template fallback" in md
    assert "ANTHROPIC_API_KEY" in md


def test_render_markdown_includes_transcript_rounds(monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Act
    md = render_thinkprint_md(transcript, result)

    # Assert — the verbatim transcript should be present for auditability.
    assert "### Round 1 ·" in md
    assert "### Round 6 ·" in md
    assert "solo founder" in md  # user's exact answer survives into the transcript


# ---------------------------------------------------------------------
# write_thinkprint — end-to-end file write
# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# contradictions field + seed-rule ranking
# ---------------------------------------------------------------------


def test_fallback_populates_contradictions_field(monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])

    # Act
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Assert — template fallback must still populate the contradictions field
    # so the dataclass is constructible and rendering doesn't blow up.
    assert result.contradictions
    assert "Template fallback" in result.contradictions


def test_render_markdown_includes_contradictions_body(monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])
    result = synthesize_profile(transcript, seed_rules=[], api_key=None)

    # Act
    md = render_thinkprint_md(transcript, result)

    # Assert — body of the contradictions section is rendered, not just the header.
    assert "## 6. Contradictions" in md
    assert result.contradictions.strip() in md


def test_rank_seed_rules_sorts_by_evidence_count_desc():
    # Arrange — three rules with 1, 3, 5 evidence turns respectively.
    def _rule_with_evidence(rid: str, n: int, tier: int = 1) -> Rule:
        return Rule(
            id=rid,
            topic=f"t-{rid}",
            statement=f"statement for {rid}",
            tier=tier,
            confidence=RuleConfidence.HIGH,
            evidence=[
                Evidence(message_id=f"m{i}", excerpt="x", source=Source.CLAUDE_MD)
                for i in range(n)
            ],
        )

    weak = _rule_with_evidence("weak", 1)
    mid = _rule_with_evidence("mid", 3)
    strong = _rule_with_evidence("strong", 5)

    # Act
    ranked = _rank_seed_rules([weak, mid, strong])

    # Assert
    assert [r.id for r in ranked] == ["strong", "mid", "weak"]


def test_rank_seed_rules_breaks_tie_on_tier_desc():
    # Arrange — same evidence count, different tiers. Tier 2 should come first.
    def _rule_tier(rid: str, tier: int) -> Rule:
        return Rule(
            id=rid,
            topic=f"t-{rid}",
            statement="s",
            tier=tier,
            confidence=RuleConfidence.HIGH,
            evidence=[Evidence(message_id="m", excerpt="x", source=Source.CLAUDE_MD)],
        )

    t1 = _rule_tier("t1", 1)
    t2 = _rule_tier("t2", 2)

    # Act
    ranked = _rank_seed_rules([t1, t2])

    # Assert
    assert [r.id for r in ranked] == ["t2", "t1"]


def test_write_thinkprint_creates_file(tmp_path: Path, monkeypatch):
    # Arrange
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    transcript = run_batch(_full_answers(), seed_rules=[])
    out = tmp_path / "out" / "thinkprint.md"

    # Act
    written = write_thinkprint(transcript, [], out, user_label="Test")

    # Assert
    assert written == out
    assert out.is_file()
    content = out.read_text(encoding="utf-8")
    assert "# Test" in content
    assert "## 1. Identity" in content
