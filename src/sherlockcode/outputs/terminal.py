"""Rich terminal output formatter for SherlockCode."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from sherlockcode.core.reviewer import ReviewResult, ReviewIssue

# Severity display config: (label, color, icon)
_SEVERITY_CONFIG = {
    "high": ("HIGH", "red", "[X]"),
    "medium": ("MEDIUM", "yellow", "[!]"),
    "low": ("LOW", "green", "[i]"),
}


class TerminalOutput:
    """Formats and displays review results in the terminal using Rich."""

    def __init__(self, color: bool = True):
        self.console = Console(highlight=False, color_system="auto" if color else None)

    def _format_issue(self, issue: ReviewIssue) -> Text:
        """Format a single issue as a Rich Text object."""
        label, color, icon = _SEVERITY_CONFIG.get(issue.severity, ("UNKNOWN", "white", "[?]"))
        text = Text()
        text.append(f"  {icon} ", style=f"bold {color}")
        text.append(f"[{issue.category}] ", style="bold")
        text.append(f"{issue.file}:{issue.line}\n", style="cyan")
        text.append(f"    {issue.description}\n", style="default")
        if issue.suggestion:
            text.append(f"    Suggest: ", style="bold dim")
            text.append(f"{issue.suggestion}\n", style="italic green")
        return text

    def _build_issue_table(self, result: ReviewResult) -> Table | None:
        """Build a Rich table of issues grouped by severity."""
        if not result.issues:
            return None

        table = Table(
            title="Issues",
            show_header=True,
            header_style="bold",
            border_style="dim",
        )
        table.add_column("Severity", style="bold", width=8)
        table.add_column("Category", width=12)
        table.add_column("Location", style="cyan")
        table.add_column("Description")

        for issue in result.issues:
            label, color, _ = _SEVERITY_CONFIG.get(issue.severity, ("???", "white", "?"))
            table.add_row(
                f"[{color}]{label}[/{color}]",
                issue.category,
                f"{issue.file}:{issue.line}",
                issue.description,
            )

        return table

    def format(self, result: ReviewResult) -> str:
        """Build the formatted terminal output string."""
        from io import StringIO
        buf = StringIO()
        console = Console(file=buf, highlight=False, force_terminal=False, color_system=None)
        self._render(console, result)
        return buf.getvalue()

    def _render(self, console: Console, result: ReviewResult):
        """Render the review result to a given console."""
        # Header
        console.print()
        console.print(Panel(
            Text("SherlockCode Review Report", style="bold"),
            border_style="blue",
        ))

        # Context info
        if result.context:
            info = Text()
            info.append("Files changed: ", style="dim")
            info.append(str(len(result.context.changed_files)), style="bold")
            if result.context.diff:
                diff_lines = result.context.diff.count("\n")
                info.append("  |  Diff lines: ", style="dim")
                info.append(f"~{diff_lines}", style="bold")
            console.print(info)
        console.print()

        # Issues by severity
        for severity in ("high", "medium", "low"):
            issues = [i for i in result.issues if i.severity == severity]
            if not issues:
                continue
            label, color, icon = _SEVERITY_CONFIG[severity]
            console.rule(f"[{color}]{label} ({len(issues)})[/{color}]")
            for issue in issues[:10]:
                console.print(self._format_issue(issue))
            if len(issues) > 10:
                console.print(f"  ... and {len(issues) - 10} more", style="dim")
            console.print()

        if not result.issues:
            console.print("[green bold]No issues found![/green bold]")
            console.print()

        # Summary
        if result.summary:
            console.rule("[bold]Summary[/bold]")
            console.print(result.summary)
            console.print()

    def display(self, result: ReviewResult):
        """Display the formatted result in the terminal."""
        self._render(self.console, result)
