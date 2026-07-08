from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, Select, TabPane, TextArea
from shared.dockerfile_lab import DockerfileLabManager

class DockerfileLabTab(TabPane):
    """Tab for Dockerfile Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Dockerfile Lab", id="tab-dockerfile", **kwargs)
        self.manager = DockerfileLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Dockerfile Generator[/bold]", classes="welcome-text")

            with Container(classes="stat-box"):
                with Horizontal():
                    with Vertical():
                        yield Label("Base Image:")
                        yield Input(placeholder="e.g. ubuntu:22.04, python:3.11-slim", id="df-base-image", value="ubuntu:latest")
                    with Vertical():
                        yield Label("Project Type:")
                        yield Select.from_values(["Generic", "Python", "Node", "Go", "Rust"], id="df-project-type", value="Generic")

                with Horizontal():
                    with Vertical():
                        yield Label("Working Directory:")
                        yield Input(placeholder="/app", id="df-workdir", value="/app")
                    with Vertical():
                        yield Label("Ports (comma-separated):")
                        yield Input(placeholder="e.g. 8080, 5432", id="df-ports")

                with Horizontal():
                    with Vertical():
                        yield Label("ENV Vars (comma-separated, KEY=VAL):")
                        yield Input(placeholder="NODE_ENV=production, PORT=8080", id="df-env-vars")

                with Horizontal():
                    with Vertical():
                        yield Label("ENTRYPOINT:")
                        yield Input(placeholder='e.g. ["python", "main.py"]', id="df-entrypoint")
                    with Vertical():
                        yield Label("CMD:")
                        yield Input(placeholder='e.g. ["npm", "start"]', id="df-cmd")

                with Horizontal():
                    yield Button("Generate Dockerfile", id="btn-df-generate", variant="primary")
                    yield Button("Clear", id="btn-df-clear", variant="error")

            with Vertical(classes="stat-box"):
                yield Label("[bold]Generated Dockerfile[/bold]")
                yield TextArea(id="df-output", read_only=True, language="dockerfile")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-df-generate":
            self.generate_dockerfile()
        elif event.button.id == "btn-df-clear":
            self.clear_form()

    def generate_dockerfile(self) -> None:
        base_image = self.query_one("#df-base-image", Input).value.strip()

        # Explicit type cast for Select to resolve mypy error
        project_type_val = self.query_one("#df-project-type", Select).value
        project_type = str(project_type_val) if project_type_val else "Generic"

        workdir = self.query_one("#df-workdir", Input).value.strip() or "/app"

        ports_str = self.query_one("#df-ports", Input).value.strip()
        ports = [p.strip() for p in ports_str.split(",")] if ports_str else None

        env_str = self.query_one("#df-env-vars", Input).value.strip()
        env_vars = [e.strip() for e in env_str.split(",")] if env_str else None

        entrypoint = self.query_one("#df-entrypoint", Input).value.strip()
        cmd = self.query_one("#df-cmd", Input).value.strip()

        output_area = self.query_one("#df-output", TextArea)

        if not base_image:
            self.notify("Base image is required.", severity="error")
            return

        try:
            result = self.manager.generate_dockerfile(
                base_image=base_image,
                project_type=project_type,
                workdir=workdir,
                ports=ports,
                env_vars=env_vars,
                entrypoint=entrypoint,
                cmd=cmd
            )
            output_area.text = result
            self.notify("Dockerfile generated successfully.")
        except Exception as e:
            output_area.text = f"Error generating Dockerfile: {e}"
            self.notify(f"Error: {e}", severity="error")

    def clear_form(self) -> None:
        self.query_one("#df-base-image", Input).value = "ubuntu:latest"
        self.query_one("#df-project-type", Select).value = "Generic"
        self.query_one("#df-workdir", Input).value = "/app"
        self.query_one("#df-ports", Input).value = ""
        self.query_one("#df-env-vars", Input).value = ""
        self.query_one("#df-entrypoint", Input).value = ""
        self.query_one("#df-cmd", Input).value = ""
        self.query_one("#df-output", TextArea).text = ""
        self.notify("Form cleared.")
