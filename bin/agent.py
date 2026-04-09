import typer
import subprocess
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    import docker
except ImportError:
    docker = None

app = typer.Typer(help="First-Class Agent Launcher")
config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")

console = Console()

def get_docker_client():
    if not docker:
        console.print("[red]Error:[/red] The 'docker' python library is not installed.")
        sys.exit(1)
    try:
        return docker.from_env()
    except Exception as e:
        console.print(f"[red]Error connecting to Docker:[/red] {e}")
        console.print("Make sure Docker is running and your user has permissions.")
        sys.exit(1)

@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(
    ctx: typer.Context,
    spec: str = typer.Option(None, "--spec", "-s", help="Path to app_spec.txt"),
    detached: bool = typer.Option(False, "--detached", "-d", help="Run the agent in the background"),
    name: str = typer.Option(None, "--name", "-n", help="Name of the agent session"),
    agent: str = typer.Option(None, "--agent", "-a", help="Which agent to use (gemini, cursor, etc)"),
    jira: str = typer.Option(None, "--jira", help="Jira ticket ID to work on (e.g., PROJ-123)")
):
    """Launch the agent."""
    console.print(Panel.fit("[bold green]Starting Agent[/bold green]", border_style="green"))

    with console.status("Verifying environment...") as status:
        # Pre-flight checks
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)  # nosec
            subprocess.run(["docker", "compose", "version"], check=True, capture_output=True)  # nosec
        except subprocess.CalledProcessError:
            console.print("[red]Docker or docker-compose is not installed or not working.[/red]")
            raise typer.Exit(1)

        status.update("Environment verified.")

    repo_root = Path(__file__).parent.parent

    # We will invoke the existing safe_run.sh which sets up workspaces, permissions, etc
    # and forwards our arguments to main.py
    safe_run_script = str(repo_root / "safe_run.sh")

    cmd = [safe_run_script]

    # Pass along known options
    if spec:
        cmd.extend(["--spec", spec])
    if agent:
        cmd.extend(["--agent", agent])
    if jira:
        cmd.extend(["--jira-ticket", jira])

    # Pass along any extra options the user provided that typer didn't catch explicitly
    cmd.extend(ctx.args)

    if detached:
        # Note: safe_run.sh doesn't natively support detached running via its own flags right now
        # except that it uses docker-compose run. We can set an env var or modify docker-compose
        # but for simplicity, we can let docker-compose in safe_run.sh run interactively in the background using subprocess.Popen
        # A more robust fix would be modifying safe_run.sh to accept a --detached flag, but we'll use Popen for now to detach the process.
        console.print("[cyan]Launching container in background...[/cyan]")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)  # nosec
        console.print("[green]Agent started in background.[/green]")
    else:
        # Interactive mode
        console.print("[cyan]Launching container...[/cyan]")
        subprocess.run(cmd)  # nosec
        console.print("[green]Agent execution finished.[/green]")


@app.command()
def list():
    """List active sessions."""
    client = get_docker_client()
    table = Table("ID", "Name", "Status", "Image")

    containers = client.containers.list(all=True)
    count = 0
    for container in containers:
        if "_agent_run" in container.name or "agent" in container.name:
            table.add_row(container.short_id, container.name, container.status, ", ".join(container.image.tags))
            count += 1

    if count == 0:
        console.print("No active agent sessions found.")
    else:
        console.print(table)


@app.command()
def attach(name: str):
    """Re-attach to a session."""
    client = get_docker_client()
    try:
        container = client.containers.get(name)
        console.print(f"[cyan]Attaching to {name}...[/cyan]")
        subprocess.run(["docker", "attach", name])  # nosec
    except docker.errors.NotFound:
        console.print(f"[red]Container {name} not found.[/red]")


@app.command()
def logs(name: str):
    """View logs."""
    client = get_docker_client()
    try:
        container = client.containers.get(name)
        console.print(f"[cyan]Fetching logs for {name}...[/cyan]")
        subprocess.run(["docker", "logs", "-f", name])  # nosec
    except docker.errors.NotFound:
        console.print(f"[red]Container {name} not found.[/red]")


@app.command()
def stop(name: str):
    """Stop a session."""
    client = get_docker_client()
    try:
        container = client.containers.get(name)
        console.print(f"[cyan]Stopping {name}...[/cyan]")
        container.stop()
        console.print(f"[green]{name} stopped successfully.[/green]")
    except docker.errors.NotFound:
        console.print(f"[red]Container {name} not found.[/red]")


@config_app.command("set")
def config_set(key: str, value: str):
    """Set a configuration value."""
    # Dummy implementation for now, in a real app this would modify agent_config.yaml
    console.print(f"Set {key} = {value}")

@config_app.command("view")
def config_view():
    """View current configuration."""
    console.print("Configuration viewer")

@config_app.command("reset")
def config_reset(key: str):
    """Reset a configuration value to default."""
    console.print(f"Reset {key}")

if __name__ == "__main__":
    app()
