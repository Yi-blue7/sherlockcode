"""Main Typer application for SherlockCode CLI."""

import typer

from sherlockcode import __version__

app = typer.Typer(
    name="sherlock",
    help="🔍 SherlockCode - AI-powered code review tool",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main_callback(
    version: bool = typer.Option(False, "--version", help="Show version"),
):
    if version:
        typer.echo(f"SherlockCode v{__version__}")
        raise typer.Exit()


from sherlockcode.cli.review import review_command
from sherlockcode.cli.fix import fix_command
from sherlockcode.cli.learn import learn_command
from sherlockcode.cli.config import config_app

app.command(name="review")(review_command)
app.command(name="fix")(fix_command)
app.command(name="learn")(learn_command)
app.add_typer(config_app, name="config", help="Manage SherlockCode configuration")
