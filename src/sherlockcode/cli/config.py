"""Configuration management commands for SherlockCode CLI."""

from pathlib import Path

import typer

from sherlockcode.config.loader import DEFAULT_CONFIG_PATH

config_app = typer.Typer(help="Manage configuration")


DEFAULT_CONFIG_CONTENT = """# SherlockCode Configuration
provider:
  default: {default_provider}
  models:
    deepseek:
      api_key: ${{DEEPSEEK_API_KEY}}
      model: deepseek-chat
      max_tokens: 4096
      endpoint: https://api.deepseek.com/v1
    claude:
      api_key: ${{CLAUDE_API_KEY}}
      model: claude-3-5-sonnet-20241022
      max_tokens: 4096
    openai:
      api_key: ${{OPENAI_API_KEY}}
      model: gpt-4o
      max_tokens: 4096

review:
  persona: default
  max_files: 50
  max_diff_lines: 5000
  ignore_patterns:
    - "*.lock"
    - "*.min.js"
    - "vendor/**"

fix:
  mode: safe
  auto_validate: true
  backup: true

learn:
  enabled: true
  max_commits: 500
  auto_learn: true

output:
  format: terminal
  color: true
  show_scores: true
"""


@config_app.command(name="init")
def config_init(
    provider: str = typer.Option("claude", "--provider", help="Default LLM provider"),
):
    """Initialize SherlockCode configuration in the current directory."""
    config_path = Path(DEFAULT_CONFIG_PATH)

    if config_path.exists():
        overwrite = typer.confirm("Config file already exists. Overwrite?")
        if not overwrite:
            typer.echo("Aborted.")
            raise typer.Exit()

    # Use format() for clean placeholder substitution
    content = DEFAULT_CONFIG_CONTENT.format(default_provider=provider)

    config_path.write_text(content)
    typer.echo(f"Config created: {config_path}")
    typer.echo(f"  Set your API key via environment variable (e.g., CLAUDE_API_KEY)")
    typer.echo(f"  Or edit {config_path} directly.")
