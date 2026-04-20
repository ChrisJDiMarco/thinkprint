"""Thinkprint CLI.

Three commands:

  thinkprint extract  --claude-dir ~/.claude --project . --chatgpt-export <path> --claude-export <path>
  thinkprint show     [--topic ...] [--limit N]
  thinkprint serve    [--db <path>]

The CLI is intentionally narrow. Anything fancier (publishing, sanitizer, swipe UI) is
deliberately not in this MVP.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from thinkprint import __version__
from thinkprint.output import render_markdown
from thinkprint.pipeline import run_extraction
from thinkprint.storage import list_topics, load_rules, save_rules

DEFAULT_DB = Path.cwd() / ".thinkprint" / "thinkprint.db"
DEFAULT_MD = Path.cwd() / "thinkprint.md"

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
