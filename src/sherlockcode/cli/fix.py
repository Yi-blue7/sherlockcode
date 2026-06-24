"""Fix command for SherlockCode CLI."""

from pathlib import Path
from typing import Optional

import typer

from sherlockcode.config.loader import load_config
from sherlockcode.core.fixer import fix_code
from sherlockcode.core.git import GitError, is_git_repo
from sherlockcode.cli.review import create_provider


def fix_command(
    preview: bool = typer.Option(True, "--preview/--apply", help="Preview fixes without applying"),
    safe: bool = typer.Option(True, "--safe/--all", help="Safe mode: only high-confidence fixes"),
    diff: Optional[str] = typer.Option(None, "--diff", help="Diff target (commit/branch)"),
    files: Optional[str] = typer.Option(None, "--files", help="Glob pattern for files"),
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider override"),
    model: Optional[str] = typer.Option(None, "--model", help="LLM model override"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path"),
):
    """Auto-fix code issues identified during review.

    Use --preview to see what would be fixed without applying changes.
    Use --apply to actually apply the fixes.
    Use --safe to only apply high-confidence fixes (default).
    Use --all to apply all fixes including risky ones.
    """
    if not is_git_repo():
        typer.echo("Error: Not in a git repository.", err=True)
        raise typer.Exit(code=4)

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

    mode = "safe" if safe else "all"
    dry_run = preview

    typer.echo(f"🔧 {'Previewing' if preview else 'Applying'} fixes ({mode} mode)...\n")

    result = fix_code(
        provider=llm,
        diff_target=diff,
        mode=mode,
        dry_run=dry_run,
    )

    # Display results
    if result.fixes:
        typer.echo(f"Found {len(result.fixes)} potential fix(es)\n")

        if result.applied:
            typer.echo("✅ Applied fixes:")
            for fix in result.applied:
                typer.echo(f"  • {fix.file}:{fix.line} [{fix.category}] ({fix.confidence}%)")
                if fix.explanation:
                    typer.echo(f"    {fix.explanation}")
            typer.echo()

        if result.skipped:
            typer.secho("⏭️  Skipped fixes:", fg="yellow")
            for fix in result.skipped:
                typer.echo(f"  • {fix.file}:{fix.line} [{fix.category}] ({fix.confidence}%)")
                typer.echo(f"    {fix.original_code[:50]}...")
            typer.echo()

        if result.failed:
            typer.secho("❌ Failed fixes:", fg="red")
            for fix in result.failed:
                typer.echo(f"  • {fix.file}:{fix.line} [{fix.category}] ({fix.confidence}%)")
            typer.echo()
    else:
        typer.secho("No fixes generated.", fg="yellow")

    # Exit codes
    if result.failed:
        raise typer.Exit(code=1)
    elif result.applied and not preview:
        typer.echo("\n✅ All fixes applied successfully!")
    elif result.applied and preview:
        typer.echo("\n💡 Run with --apply to apply these fixes.")
