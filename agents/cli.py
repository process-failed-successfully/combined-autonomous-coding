import typer
import sys
import os
from rich.console import Console
from rich.panel import Panel
from agents.pre_flight import PreFlightCheck
from agents.config_manager import ConfigManager

app = typer.Typer(
    name="agent",
    help="Autonomous Coding Agent CLI Launcher",
    add_completion=False,
    no_args_is_help=True
)
config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")

console = Console()

@app.command()
def run(
    detached: bool = typer.Option(False, "--detached", "-d", help="Run in detached mode"),
    name: str = typer.Option(None, "--name", "-n", help="Name for the session"),
    jira: str = typer.Option(None, "--jira", "-j", help="Jira ticket key to work on"),
    skip_checks: bool = typer.Option(False, "--skip-checks", help="Skip pre-flight checks (DEV ONLY)")
):
    """
    Launch the Autonomous Coding Agent.
    """
    console.print(Panel.fit(
        "[bold blue]Autonomous Coding Agent[/bold blue]\n"
        "[dim]v0.4.0 - First-Class Launcher[/dim]",
        border_style="blue"
    ))

    # Pre-flight checks
    if not skip_checks:
        checker = PreFlightCheck()
        if not checker.run_checks():
            console.print("\n[bold red]Pre-flight checks failed. Please fix the issues above.[/bold red]")
            raise typer.Exit(code=1)
        console.print("\n[bold green]Checks passed! Launching agent...[/bold green]")
    else:
        console.print("\n[bold yellow]Skipping pre-flight checks...[/bold yellow]")
    
    # Placeholder for actual launch logic
    if jira:
        console.print(f"[cyan]Mode: Jira ({jira})[/cyan]")
    else:
        console.print("[cyan]Mode: Autonomous[/cyan]")

    if detached:
        console.print("[yellow]Detached mode not yet implemented.[/yellow]")
    
    # TODO: Actual container launch logic here

@app.command()
def list():
    """
    List active agent sessions.
    """
    console.print("[dim]No active sessions found (Placeholder).[/dim]")

@config_app.command("list-keys")
def config_list_keys():
    """List all configurable keys."""
    ConfigManager().list_keys()

@config_app.command("set")
def config_set(key: str, value: str):
    """Set a configuration value."""
    ConfigManager().set_value(key, value)

@config_app.command("list-models")
def config_list_models(agent: str = typer.Option(None, "--agent", help="Filter by agent type")):
    """List available models."""
    ConfigManager().list_models(agent)

if __name__ == "__main__":
    app()
