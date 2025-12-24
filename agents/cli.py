import typer
import sys
import os
import logging
import random
import time
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler
from agents.pre_flight import PreFlightCheck
from agents.config_manager import ConfigManager
from agents.session_manager import SessionManager

app = typer.Typer(
    name="agent",
    help="Autonomous Coding Agent CLI Launcher",
    add_completion=False,
    no_args_is_help=True
)
config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")

console = Console()
session_manager = SessionManager()

def setup_logging(verbose: bool = False):
    """Configure logging with Rich."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)],
        force=True
    )

def generate_name() -> str:
    adjectives = ["swift", "calm", "bright", "eager", "brave", "quiet", "wise", "bold"]
    nouns = ["fox", "eagle", "lion", "bear", "hawk", "owl", "wolf", "tiger"]
    return f"{random.choice(adjectives)}-{random.choice(nouns)}-{int(time.time()) % 1000}"

@app.command()
def run(
    detached: bool = typer.Option(False, "--detached", "-d", help="Run in detached mode"),
    name: str = typer.Option(None, "--name", "-n", help="Name for the session"),
    jira: str = typer.Option(None, "--jira", "-j", help="Jira ticket key to work on"),
    skip_checks: bool = typer.Option(False, "--skip-checks", help="Skip pre-flight checks (DEV ONLY)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    model: str = typer.Option(None, "--model", "-m", help="Override model selection"),
    max_iterations: int = typer.Option(None, "--max-iterations", "-i", help="Max iterations")
):
    """
    Launch the Autonomous Coding Agent.
    """
    setup_logging(verbose)
    logger = logging.getLogger("agent")

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
        console.print("\n[bold green]Checks passed![/bold green]")
    else:
        console.print("\n[bold yellow]Skipping pre-flight checks...[/bold yellow]")

    # Construct Command
    cmd = [sys.executable, "main.py"]
    if jira:
        cmd.extend(["--jira-ticket", jira])
    if verbose:
        cmd.append("--verbose")
    if model:
        cmd.extend(["--model", model])
    if max_iterations:
        cmd.extend(["--max-iterations", str(max_iterations)])
    
    # Session Management
    if not name:
        name = generate_name()

    if detached:
        console.print(f"[yellow]Launching detached session: {name}[/yellow]")
        try:
            session = session_manager.start_session(name, cmd, detached=True)
            console.print(f"[green]Session started![/green] (PID: {session['pid']})")
            console.print(f"Log file: {session['log_file']}")
            console.print(f"Use [bold]agent logs {name}[/bold] to view output.")
        except Exception as e:
            console.print(f"[red]Failed to start session: {e}[/red]")
            raise typer.Exit(code=1)
    else:
        console.print(f"[cyan]Running session: {name}[/cyan]")
        try:
            ret = session_manager.start_session(name, cmd, detached=False)
            if ret != 0:
                raise typer.Exit(code=ret)
        except Exception as e:
            console.print(f"[red]Error running agent: {e}[/red]")
            raise typer.Exit(code=1)

@app.command()
def list():
    """
    List active agent sessions.
    """
    sessions = session_manager.list_sessions()
    if not sessions:
        console.print("[dim]No active sessions found.[/dim]")
        return

    table = Table(title="Active Agent Sessions")
    table.add_column("Name", style="cyan")
    table.add_column("PID", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Started", style="blue")
    table.add_column("Command", style="dim")

    for s in sessions:
        status_style = "green" if s["status"] == "running" else "red"
        start_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s["start_time"]))
        cmd_str = " ".join(s["command"])
        table.add_row(
            s["name"], 
            str(s["pid"]), 
            f"[{status_style}]{s['status']}[/{status_style}]", 
            start_str,
            cmd_str[:30] + "..." if len(cmd_str) > 30 else cmd_str
        )
    
    console.print(table)

@app.command()
def stop(name: str):
    """
    Stop a detached agent session.
    """
    success, msg = session_manager.stop_session(name)
    if success:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")

@app.command()
def attach(name: str):
    """
    Attach to a session (stream logs).
    """
    logs(name, follow=True)

@app.command()
def logs(name: str, lines: int = 50, follow: bool = False):
    """
    View logs for a session.
    """
    log_path = session_manager.get_log_path(name)
    if not log_path:
        console.print(f"[red]Session '{name}' not found.[/red]")
        return

    if not log_path.exists():
        console.print(f"[red]Log file not found: {log_path}[/red]")
        return

    console.print(f"[blue]Displaying logs for {name} ({log_path}):[/blue]")
    
    # Simple tail implementation
    try:
        if follow:
            subprocess.run(["tail", "-f", "-n", str(lines), str(log_path)])
        else:
            subprocess.run(["tail", "-n", str(lines), str(log_path)])
    except KeyboardInterrupt:
        pass


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
