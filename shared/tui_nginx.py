from textual.app import ComposeResult
from textual.widgets import Input, Button, Label, Select, TextArea, Static
from textual.containers import Vertical, Horizontal, Container, VerticalScroll
from textual import on

from shared.nginx_lab import NginxLabManager

class NginxLabTab(Container):
    """Tab for generating Nginx configurations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = NginxLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Nginx Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Config Type:")
                yield Select.from_values(["Reverse Proxy", "Static Site", "Load Balancer"], id="nginx-type-select", value="Reverse Proxy")

            # Reverse Proxy Container
            with Vertical(id="nginx-proxy-container", classes="stat-box"):
                yield Label("Domain Name:")
                yield Input(placeholder="e.g. example.com", id="nginx-proxy-domain")
                yield Label("Port:")
                yield Input(placeholder="e.g. 8080", id="nginx-proxy-port", type="integer")

            # Static Site Container
            with Vertical(id="nginx-static-container", classes="stat-box", styles="display: none;"):
                yield Label("Domain Name:")
                yield Input(placeholder="e.g. example.com", id="nginx-static-domain")
                yield Label("Root Path:")
                yield Input(placeholder="e.g. /var/www/html", id="nginx-static-path")

            # Load Balancer Container
            with Vertical(id="nginx-lb-container", classes="stat-box", styles="display: none;"):
                yield Label("Domain Name:")
                yield Input(placeholder="e.g. example.com", id="nginx-lb-domain")
                yield Label("Upstream Servers (comma separated):")
                yield Input(placeholder="e.g. 10.0.0.1:80, 10.0.0.2:80", id="nginx-lb-upstreams")

            with Horizontal(classes="stat-box"):
                yield Button("Generate Config", id="btn-nginx-generate", variant="primary")
                yield Button("Copy to Clipboard", id="btn-nginx-copy", variant="success")

            with VerticalScroll(classes="stat-box"):
                yield Label("[bold]Generated Configuration:[/bold]")
                yield TextArea(id="nginx-output", read_only=True, language="nginx")

    @on(Select.Changed, "#nginx-type-select")
    def on_type_changed(self, event: Select.Changed) -> None:
        # Hide all containers
        self.query_one("#nginx-proxy-container").styles.display = "none"
        self.query_one("#nginx-static-container").styles.display = "none"
        self.query_one("#nginx-lb-container").styles.display = "none"

        # Show selected container
        if event.value == "Reverse Proxy":
            self.query_one("#nginx-proxy-container").styles.display = "block"
        elif event.value == "Static Site":
            self.query_one("#nginx-static-container").styles.display = "block"
        elif event.value == "Load Balancer":
            self.query_one("#nginx-lb-container").styles.display = "block"

    @on(Button.Pressed, "#btn-nginx-generate")
    def on_generate(self) -> None:
        config_type = self.query_one("#nginx-type-select", Select).value
        output = ""

        if config_type == "Reverse Proxy":
            domain = self.query_one("#nginx-proxy-domain", Input).value
            port_str = self.query_one("#nginx-proxy-port", Input).value
            if not domain or not port_str:
                self.notify("Domain and Port are required.", severity="error")
                return
            output = self.manager.generate_proxy(domain, int(port_str))

        elif config_type == "Static Site":
            domain = self.query_one("#nginx-static-domain", Input).value
            path = self.query_one("#nginx-static-path", Input).value
            if not domain or not path:
                self.notify("Domain and Path are required.", severity="error")
                return
            output = self.manager.generate_static(domain, path)

        elif config_type == "Load Balancer":
            domain = self.query_one("#nginx-lb-domain", Input).value
            upstreams_str = self.query_one("#nginx-lb-upstreams", Input).value
            if not domain or not upstreams_str:
                self.notify("Domain and Upstream Servers are required.", severity="error")
                return
            upstreams = [u.strip() for u in upstreams_str.split(",") if u.strip()]
            output = self.manager.generate_loadbalancer(domain, upstreams)

        text_area = self.query_one("#nginx-output", TextArea)
        text_area.text = output
        self.notify("Configuration generated.", severity="info")

    @on(Button.Pressed, "#btn-nginx-copy")
    def on_copy(self) -> None:
        text = self.query_one("#nginx-output", TextArea).text
        if text:
            try:
                self.app.copy_to_clipboard(text)
                self.notify("Copied to clipboard!", severity="success")
            except Exception as e:
                self.notify(f"Could not copy: {e}", severity="error")
        else:
            self.notify("Nothing to copy.", severity="warning")
