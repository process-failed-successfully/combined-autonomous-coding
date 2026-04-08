from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, TextArea, Input

from shared.compose2k8s_lab import Compose2K8sManager


class Compose2K8sLabTab(Vertical):
    """TUI Tab for Docker Compose to Kubernetes Lab."""

    def __init__(self, project_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = Compose2K8sManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content"):
            yield Label("[bold]Docker Compose to Kubernetes[/bold] - Convert docker-compose.yml to K8s Manifests", classes="tab-title")

            with Horizontal(classes="action-bar"):
                yield Button("Convert", id="btn-compose2k8s-convert", variant="primary")
                yield Button("Clear", id="btn-compose2k8s-clear", variant="warning")
                yield Button("Load Example", id="btn-compose2k8s-example", variant="default")

            with Horizontal():
                with Vertical(classes="panel"):
                    yield Label("Input docker-compose.yml:")
                    yield TextArea(id="compose2k8s-input-area", language="yaml")

                with Vertical(classes="panel"):
                    yield Label("Generated K8s Manifests:")
                    yield TextArea(id="compose2k8s-output-area", language="yaml", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-compose2k8s-convert":
            self.convert_compose()
        elif event.button.id == "btn-compose2k8s-clear":
            self.clear_all()
        elif event.button.id == "btn-compose2k8s-example":
            self.load_example()

    def convert_compose(self) -> None:
        input_area = self.query_one("#compose2k8s-input-area", TextArea)
        compose_content = input_area.text.strip()

        if not compose_content:
            self.app.notify("docker-compose.yml content is required.", severity="error")
            return

        try:
            k8s_yaml = self.manager.generate_k8s_manifests(compose_content)
            self.query_one("#compose2k8s-output-area", TextArea).text = k8s_yaml
            self.app.notify("Successfully converted to K8s Manifests.")
        except Exception as e:
            self.app.notify(f"Parsing Error: {e}", severity="error")

    def clear_all(self) -> None:
        self.query_one("#compose2k8s-input-area", TextArea).text = ""
        self.query_one("#compose2k8s-output-area", TextArea).text = ""
        self.app.notify("Fields cleared.")

    def load_example(self) -> None:
        example = '''version: "3.9"
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
    environment:
      - NGINX_PORT=80
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
'''
        self.query_one("#compose2k8s-input-area", TextArea).text = example
        self.query_one("#compose2k8s-output-area", TextArea).text = ""
        self.app.notify("Example loaded.")
