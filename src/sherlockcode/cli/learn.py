"""Learn command for SherlockCode CLI."""

from pathlib import Path
from typing import Optional

import typer

from sherlockcode.config.loader import load_config
from sherlockcode.core.learner import Learner
from sherlockcode.core.git import GitError, is_git_repo
from sherlockcode.cli.review import create_provider


def learn_command(
    since: Optional[str] = typer.Option(None, "--since", help="Start date for learning (YYYY-MM-DD)"),
    focus: Optional[str] = typer.Option(None, "--focus", help="Focus area (bugs|style|architecture|performance|security)"),
    stats: bool = typer.Option(False, "--stats", help="Show learning statistics"),
    export: Optional[Path] = typer.Option(None, "--export", help="Export knowledge to file"),
    reset: bool = typer.Option(False, "--reset", help="Reset all learned data"),
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider override"),
    model: Optional[str] = typer.Option(None, "--model", help="LLM model override"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path"),
):
    """Learn patterns from git history and code.

    Analyze commits to extract:
    - Coding style conventions
    - Bug patterns and fixes
    - Design patterns
    - Team conventions

    Use --stats to view current knowledge base.
    Use --export to save knowledge to a file.
    Use --reset to clear all learned data.
    """
    if not is_git_repo():
        typer.echo("Error: Not in a git repository.", err=True)
        raise typer.Exit(code=4)

    learner = Learner()

    # Handle reset
    if reset:
        if typer.confirm("Are you sure you want to reset all learned data?"):
            learner.reset()
            typer.secho("✅ Knowledge base reset.", fg="green")
        else:
            typer.echo("Cancelled.")
        raise typer.Exit()

    # Handle stats
    if stats:
        knowledge = learner.get_knowledge()
        stats_data = learner.get_stats()

        typer.echo("📊 SherlockCode Learning Statistics")
        typer.echo("─" * 40)
        typer.echo(f"Last updated: {stats_data['last_updated'] or 'Never'}")
        typer.echo(f"Bug patterns: {stats_data['bug_patterns_count']}")
        typer.echo(f"Design patterns: {stats_data['design_patterns_count']}")
        typer.echo(f"Conventions: {stats_data['conventions_count']}")
        typer.echo()

        if knowledge.bug_patterns:
            typer.echo("🔧 Top Bug Patterns:")
            for pattern in sorted(knowledge.bug_patterns, key=lambda p: p.frequency, reverse=True)[:5]:
                typer.echo(f"  • {pattern.pattern_id}: {pattern.description} (seen {pattern.frequency}x)")

        if knowledge.style_rules.variables != "snake_case":
            typer.echo()
            typer.echo("🎨 Detected Style Rules:")
            sr = knowledge.style_rules
            typer.echo(f"  Variables: {sr.variables}")
            typer.echo(f"  Functions: {sr.functions}")
            typer.echo(f"  Classes: {sr.classes}")
            typer.echo(f"  Indent: {sr.indent} spaces")

        raise typer.Exit()

    # Handle export
    if export:
        path = learner.export(export)
        typer.secho(f"✅ Knowledge exported to: {path}", fg="green")
        raise typer.Exit()

    # Learn from git history
    config = load_config(config_path)

    if provider:
        config.provider.default = provider
    if model:
        if config.provider.default in config.provider.models:
            config.provider.models[config.provider.default].model = model

    try:
        llm = create_provider(config)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=3)

    typer.echo("🧠 Learning from git history...\n")

    knowledge = learner.learn_from_provider(
        provider=llm,
        since=since,
    )

    typer.secho("✅ Learning complete!", fg="green")
    typer.echo()
    typer.echo(f"Extracted:")
    typer.echo(f"  • {len(knowledge.bug_patterns)} bug patterns")
    typer.echo(f"  • {len(knowledge.design_patterns)} design patterns")
    typer.echo(f"  • {len(knowledge.conventions)} conventions")
    typer.echo()
    typer.echo(f"Knowledge saved to: {learner.knowledge_file}")
    typer.echo("Run 'sherlock learn --stats' to view learned patterns.")
