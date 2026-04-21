"""Thinkprint CLI.

Commands:

  thinkprint interview                              # primary — runs Q&A, writes thinkprint.md
  thinkprint interview --answers answers.json       # batch mode (non-interactive)
  thinkprint extract   --claude-dir ~/.claude ...   # seed-only: scrapes configs into rules
  thinkprint show      [--topic ...] [--limit N]
  thinkprint topics
  thinkprint serve     [--db <path>]

A Thinkprint is built through structured Q&A elicitation, not extraction alone.
`extract` is a seed step; `interview` is the product.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from thinkprint import __version__
from thinkprint.interview import (
    load_answers,
    run_batch,
    run_interactive,
    save_transcript,
)
from thinkprint.output import render_markdown
from thinkprint.pipeline import run_extraction
from thinkprint.storage import list_topics, load_rules, save_rules
from thinkprint.synthesis import write_thinkprint

DEFAULT_DB = Path.cwd() / ".thinkprint" / "thinkprint.db"
DEFAULT_MD = Path.cwd() / "thinkprint.md"
DEFAULT_TRANSCRIPT = Path.cwd() / ".thinkprint" / "interview.json"

console = Console()


@click.group()
@click.version_option(__version__, prog_name="thinkprint")
def cli() -> None:
    """Thinkprint — extract behavioral rules from your AI history, serve over MCP."""


@cli.command()
@click.option(
    "--claude-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Path to your ~/.claude directory (auto-detected if omitted).",
)
@click.option(
    "--project",
    "project_dirs",
    multiple=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Project root(s) to scan for CLAUDE.md / .cursorrules / .windsurfrules.",
)
@click.option(
    "--chatgpt-export",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to ChatGPT conversations.json export.",
)
@click.option(
    "--claude-export",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to Claude conversations export JSON.",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_DB,
    show_default=True,
    help="SQLite DB to write rules to.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_MD,
    show_default=True,
    help="Markdown output path.",
)
@click.option("--max-clusters", type=int, default=None, help="Override autoselected k.")
@click.option(
    "--no-llm",
    is_flag=True,
    default=False,
    help="Skip Tier 2 synthesis (no Anthropic API calls). Tier 1 only.",
)
def extract(
    claude_dir: Path | None,
    project_dirs: tuple[Path, ...],
    chatgpt_export: Path | None,
    claude_export: Path | None,
    db_path: Path,
    out_path: Path,
    max_clusters: int | None,
    no_llm: bool,
) -> None:
    """Run the extraction pipeline and write rules to SQLite + markdown."""
    console.print("[bold cyan]Thinkprint[/bold cyan] — extracting your profile…")

    rules, stats = run_extraction(
        claude_dir=claude_dir,
        project_dirs=list(project_dirs),
        chatgpt_export=chatgpt_export,
        claude_export=claude_export,
        max_clusters=max_clusters,
        use_llm=not no_llm,
    )

    save_rules(db_path, rules, replace=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(rules), encoding="utf-8")

    console.print()
    console.print("[bold green]Done.[/bold green]")
    console.print(stats.to_summary())
    console.print(f"\n[dim]DB:[/dim] {db_path}")
    console.print(f"[dim]Markdown:[/dim] {out_path}")
    if not chatgpt_export and not claude_export and not rules:
        console.print(
            "\n[yellow]Tip:[/yellow] no chat exports given and no config files found. "
            "Run with --chatgpt-export and/or --claude-export to capture Tier 2 rules."
        )


@cli.command()
@click.option(
    "--claude-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Path to your ~/.claude directory (optional — used as seed context).",
)
@click.option(
    "--project",
    "project_dirs",
    multiple=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Project root(s) to scan for CLAUDE.md / .cursorrules (seed context).",
)
@click.option(
    "--answers",
    "answers_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Batch mode: JSON file of {question_id: answer} — skip interactive prompts.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_MD,
    show_default=True,
    help="Thinkprint markdown output path.",
)
@click.option(
    "--transcript",
    "transcript_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_TRANSCRIPT,
    show_default=True,
    help="Where to save the raw interview transcript JSON.",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_DB,
    show_default=True,
    help="SQLite DB for seed rules.",
)
@click.option(
    "--label",
    default="Thinkprint",
    show_default=True,
    help="Title for the generated markdown (e.g. 'Thinkprint: Chris D.').",
)
def interview(
    claude_dir: Path | None,
    project_dirs: tuple[Path, ...],
    answers_path: Path | None,
    out_path: Path,
    transcript_path: Path,
    db_path: Path,
    label: str,
) -> None:
    """Run the Thinkprint Q&A interview and write the synthesized profile.

    The interview is the primary way to build a Thinkprint. Seed extraction
    from config files is used only to prime implicit observations.
    """
    console.print(f"[bold cyan]Thinkprint[/bold cyan] — interview · {label}")

    # 1. Gather seed rules (silent — extraction is a pre-step, not the output).
    seed_rules, _stats = run_extraction(
        claude_dir=claude_dir,
        project_dirs=list(project_dirs),
        chatgpt_export=None,
        claude_export=None,
        use_llm=False,
    )
    if seed_rules:
        save_rules(db_path, seed_rules, replace=True)
        console.print(f"[dim]Seed context:[/dim] {len(seed_rules)} rules from configs")

    # 2. Run the interview — batch or interactive.
    if answers_path:
        answers = load_answers(answers_path)
        transcript = run_batch(answers, seed_rules)
        console.print(f"[dim]Batch interview:[/dim] {len(transcript.rounds)} rounds")
    else:
        transcript = run_interactive(seed_rules)

    save_transcript(transcript, transcript_path)

    # 3. Synthesize the profile and write markdown.
    final_path = write_thinkprint(
        transcript,
        seed_rules,
        out_path,
        user_label=label,
    )

    console.print()
    console.print("[bold green]Thinkprint written.[/bold green]")
    console.print(f"[dim]Profile:[/dim] {final_path}")
    console.print(f"[dim]Transcript:[/dim] {transcript_path}")
    console.print(f"[dim]Seed DB:[/dim] {db_path}")


@cli.command()
@click.option("--topic", default="", help="Filter by topic substring.")
@click.option("--limit", type=int, default=20, show_default=True)
@click.option(
    "--db",
    "db_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_DB,
    show_default=True,
)
def show(topic: str, limit: int, db_path: Path) -> None:
    """Print the current Thinkprint rules to the terminal."""
    if not db_path.is_file():
        console.print(f"[red]No DB at {db_path}.[/red] Run `thinkprint extract` first.")
        sys.exit(1)

    rules = load_rules(db_path, topic=topic or None, limit=limit)
    if not rules:
        console.print("[yellow]No rules match.[/yellow]")
        return

    table = Table(title=f"Thinkprint ({len(rules)} rules)", show_lines=False)
    table.add_column("Topic", style="cyan", no_wrap=True)
    table.add_column("Tier", justify="center")
    table.add_column("Conf.", justify="center")
    table.add_column("Statement")

    for r in rules:
        table.add_row(r.topic, str(r.tier), r.confidence.value, r.statement)
    console.print(table)


@cli.command()
@click.option(
    "--db",
    "db_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_DB,
    show_default=True,
)
def topics(db_path: Path) -> None:
    """List all topics and the number of rules each has."""
    if not db_path.is_file():
        console.print(f"[red]No DB at {db_path}.[/red] Run `thinkprint extract` first.")
        sys.exit(1)
    rows = list_topics(db_path)
    table = Table(title="Topics")
    table.add_column("Topic", style="cyan")
    table.add_column("Rules", justify="right")
    for topic, n in rows:
        table.add_row(topic, str(n))
    console.print(table)


@cli.command()
@click.option(
    "--db",
    "db_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_DB,
    show_default=True,
)
def serve(db_path: Path) -> None:
    """Start the Thinkprint MCP server (stdio)."""
    from thinkprint.mcp_server import run_server

    if not db_path.is_file():
        console.print(
            f"[yellow]Warning:[/yellow] DB at {db_path} doesn't exist yet. "
            "MCP tools will return empty results until you run `thinkprint extract`."
        )
    run_server(db_path)


if __name__ == "__main__":
    cli()
