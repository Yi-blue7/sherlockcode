"""Review command for SherlockCode CLI."""

from pathlib import Path
from typing import Optional

import typer

from sherlockcode.config.loader import load_config
from sherlockcode.core.git import is_git_repo
from sherlockcode.core.reviewer import review_code
from sherlockcode.outputs.terminal import TerminalOutput
from sherlockcode.outputs.markdown import MarkdownOutput
from sherlockcode.providers import create_provider


def review_command(
    diff: Optional[str] = typer.Option(None, "--diff", help="Diff target (commit/branch)"),
    pr: Optional[int] = typer.Option(None, "--pr", help="GitHub PR number"),
    files: Optional[str] = typer.Option(None, "--files", help="Glob pattern for files"),
    persona: str = typer.Option("default", "--persona", help="Review persona"),
    output: str = typer.Option("terminal", "--output", help="Output format"),
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider override"),
    model: Optional[str] = typer.Option(None, "--model", help="LLM model override"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path"),
):
    """Review code changes using AI."""
    if not is_git_repo():
        typer.echo("Error: Not in a git repository.", err=True)
        raise typer.Exit(code=4)

    config = load_config(config_path)

    if provider:
        config.provider.default = provider
    if model:
        if config.provider.default in config.provider.models:
            config.provider.models[config.provider.default].model = model

    provider_config = config.provider
    model_config = provider_config.models[provider_config.default]
    api_key = model_config.get_api_key()

    if not api_key:
        typer.echo(
            f"Error: No API key found for provider '{provider_config.default}'. "
            f"Run 'sherlock config init' to set up.",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        llm = create_provider(
            name=provider_config.default,
            api_key=api_key,
            model=model_config.model,
            max_tokens=model_config.max_tokens,
            endpoint=model_config.endpoint,
        )
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=3)

    typer.echo(f"Reviewing code with {config.provider.default}...\n")

    result = review_code(
        llm,
        diff_target=diff,
        persona=persona,
        max_diff_lines=config.review.max_diff_lines,
        max_files=config.review.max_files,
    )

    if output == "markdown":
        md = MarkdownOutput()
        report = md.format(result)
        typer.echo(report)
    else:
        terminal = TerminalOutput(color=config.output.color)
        terminal.display(result)

    has_high = any(i.severity == "high" for i in result.issues)
    if has_high:
        raise typer.Exit(code=1)
