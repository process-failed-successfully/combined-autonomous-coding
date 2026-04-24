import typer
import subprocess
import sys
import yaml
from pathlib import Path

# Ensure we can import from shared
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config_loader import get_config_path, ensure_config_exists
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

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
        client.containers.get(name)
        console.print(f"[cyan]Attaching to {name}...[/cyan]")
        subprocess.run(["docker", "attach", name])  # nosec
    except docker.errors.NotFound:
        console.print(f"[red]Container {name} not found.[/red]")


@app.command()
def logs(name: str):
    """View logs."""
    client = get_docker_client()
    try:
        client.containers.get(name)
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
    ensure_config_exists()
    path = get_config_path()
    if not path:
        console.print("[red]Error: Could not determine configuration path.[/red]")
        return

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        parsed_value: bool | int | float | str
        # Parse basic types
        if value.lower() in ("true", "yes"):
            parsed_value = True
        elif value.lower() in ("false", "no"):
            parsed_value = False
        else:
            try:
                parsed_value = int(value)
            except ValueError:
                try:
                    parsed_value = float(value)
                except ValueError:
                    parsed_value = value

        keys = key.split('.')
        current = data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = parsed_value

        with open(path, "w") as f:
            yaml.dump(data, f, indent=2, sort_keys=False)
        console.print(f"[green]Set {key} = {parsed_value}[/green]")
    except Exception as e:
        console.print(f"[red]Error setting configuration:[/red] {e}")


@config_app.command("view")
def config_view():
    """View current configuration."""
    path = get_config_path()
    if not path or not path.exists():
        console.print("[yellow]No configuration file found.[/yellow]")
        return
    try:
        from rich.syntax import Syntax
        with open(path, "r") as f:
            content = f.read()
        syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"Configuration: {path}"))
    except Exception as e:
        console.print(f"[red]Error reading configuration:[/red] {e}")


@config_app.command("list-keys")
def config_list_keys():
    """List all configurable settings with descriptions and defaults."""
    import dataclasses
    from shared.config import Config

    table = Table("Key", "Type", "Default")

    # Exclude internal fields not meant for user configuration via CLI
    exclude_keys = {
        "project_dir", "agent_id", "sprint_id", "jira_ticket_key",
        "jira_spec_content", "spec_file", "jira"
    }

    for field in dataclasses.fields(Config):
        if field.name in exclude_keys:
            continue

        type_name = str(field.type).replace("typing.", "")
        if hasattr(field.type, "__name__"):
            type_name = field.type.__name__

        default_val = "None"
        if field.default is not dataclasses.MISSING:
            default_val = str(field.default)
        elif field.default_factory is not dataclasses.MISSING:
            default_val = "Factory"

        table.add_row(field.name, type_name, default_val)

    console.print(table)


@config_app.command("reset")
def config_reset(key: str):
    """Reset a configuration value to default."""
    path = get_config_path()
    if not path or not path.exists():
        console.print("[yellow]No configuration file found.[/yellow]")
        return
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        keys = key.split('.')
        current = data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                console.print(f"[yellow]Key {key} not found.[/yellow]")
                return
            current = current[k]

        if keys[-1] in current:
            del current[keys[-1]]
            with open(path, "w") as f:
                yaml.dump(data, f, indent=2, sort_keys=False)
            console.print(f"[green]Reset {key}[/green]")
        else:
            console.print(f"[yellow]Key {key} not found.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error resetting configuration:[/red] {e}")


if __name__ == "__main__":
    app()
