"""End-to-end extraction pipeline. Orchestrates extractors → filters → archaeology → storage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from thinkprint.archaeology import (
    cluster_messages,
    detect_acceptance_signals,
    detect_rephrase_events,
    synthesize_rules,
)
from thinkprint.extractors import (
    extract_config_rules,
    parse_chatgpt_export,
    parse_claude_export,
)
from thinkprint.filter import flag_injection_candidates, strip_noise
from thinkprint.models import Message, Rule


@dataclass
class ExtractionStats:
    config_rules: int
    raw_messages: int
    kept_messages: int
    flagged_injection: int
    clusters: int
    tier2_rules: int

    def to_summary(self) -> str:
        return (
            f"Tier 1 rules from config files: {self.config_rules}\n"
            f"Messages parsed: {self.raw_messages} → kept after noise filter: {self.kept_messages}\n"
            f"Injection candidates flagged (soft-quarantined): {self.flagged_injection}\n"
            f"Topical clusters: {self.clusters}\n"
            f"Tier 2 rules synthesized: {self.tier2_rules}"
        )


def _excluded_for_llm(decisions, threshold: float = 0.85) -> set[str]:
    return {d.message_id for d in decisions if d.injection_score >= threshold}


def run_extraction(
    claude_dir: Path | None,
    project_dirs: list[Path],
    chatgpt_export: Path | None,
    claude_export: Path | None,
    *,
    max_clusters: int | None = None,
    use_llm: bool = True,
) -> tuple[list[Rule], ExtractionStats]:
    """Run the full extraction pipeline. Returns (rules, stats)."""
    # Tier 1
    config_rules = extract_config_rules(claude_dir=claude_dir, project_dirs=project_dirs)

    # Tier 2 messages
    messages: list[Message] = []
    if chatgpt_export and chatgpt_export.is_file():
        messages.extend(parse_chatgpt_export(chatgpt_export))
    if claude_export and claude_export.is_file():
        messages.extend(parse_claude_export(claude_export))

    raw_count = len(messages)
    kept, _noise_decisions = strip_noise(messages)
    injection_decisions = flag_injection_candidates(kept)
    excluded_ids = _excluded_for_llm(injection_decisions)
    safe_for_llm = [m for m in kept if m.id not in excluded_ids]

    clusters = cluster_messages(safe_for_llm, k=max_clusters)
    tier2_rules: list[Rule] = []

    if use_llm and clusters:
        msg_by_id = {m.id: m for m in safe_for_llm}
        for cluster in clusters:
            cluster_msgs = [msg_by_id[mid] for mid in cluster.message_ids if mid in msg_by_id]
            if not cluster_msgs:
                continue
            rephrases = detect_rephrase_events(cluster_msgs)
            acceptances = detect_acceptance_signals(cluster_msgs)
            tier2_rules.extend(
                synthesize_rules(cluster, cluster_msgs, rephrases, acceptances)
            )

    all_rules = config_rules + tier2_rules
    stats = ExtractionStats(
        config_rules=len(config_rules),
        raw_messages=raw_count,
        kept_messages=len(kept),
        flagged_injection=sum(1 for d in injection_decisions if d.flagged_injection),
        clusters=len(clusters),
        tier2_rules=len(tier2_rules),
    )
    return all_rules, stats
