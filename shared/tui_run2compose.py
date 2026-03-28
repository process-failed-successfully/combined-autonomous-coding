from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import TextArea, Button, Static
from shared.run2compose_lab import Run2ComposeManager


class Run2ComposeLabTab(Container):
    """TUI Tab for converting docker run commands to docker-compose.yml."""

    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir
        self.manager = Run2ComposeManager()

    def compose(self) -> ComposeResult:
        yield Static("[bold]Run2Compose Lab[/bold] - Convert docker run commands to Docker Compose", classes="tab-title")
        with Horizontal():
            with VerticalScroll():
                yield Static("Docker Run Command:", classes="label")
                self.input_area = TextArea(text="docker run -d --name web -p 80:80 nginx", language="bash")
                yield self.input_area
                yield Button("Convert", id="btn_convert", variant="primary")

            with VerticalScroll():
                yield Static("Docker Compose YAML:", classes="label")
                self.output_area = TextArea(language="yaml", read_only=True)
                yield self.output_area

    def on_mount(self) -> None:
        self.input_area.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_convert":
            self.convert()

    def convert(self) -> None:
        command_str = self.input_area.text
        if not command_str.strip():
            self.output_area.text = "Error: Input is empty."
            return

        result = self.manager.parse(command_str)
        if "error" in result:
            self.output_area.text = result["error"]
        else:
            try:
                yaml_str = self.manager.to_yaml(result["compose"])
                self.output_area.text = yaml_str
            except Exception as e:
                self.output_area.text = f"Error generating YAML: {e}"
