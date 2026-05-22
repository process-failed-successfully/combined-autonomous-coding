"""
Nginx Configuration Lab TUI Tab
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Input, Label, Select, TextArea
from shared.nginx_lab import NginxLabManager


class NginxLabTab(Vertical):
    def compose(self) -> ComposeResult:
        self.manager = NginxLabManager()

        yield Label("Nginx Configuration Generator", classes="tab-title")
        yield Label("Generate boilerplate Nginx configurations.")

        yield Horizontal(
            Label("Type: "),
            Select([("Reverse Proxy", "proxy"), ("Static Server", "static"), ("Load Balancer", "loadbalancer")], id="nginx_type", value="proxy"),
            classes="input-row"
        )

        yield Horizontal(
            Label("Server Name: "),
            Input(placeholder="example.com", id="nginx_server_name", value="example.com"),
            classes="input-row"
        )

        yield Horizontal(
            Label("Port: "),
            Input(placeholder="80", id="nginx_port", value="80"),
            classes="input-row"
        )

        # Context specific inputs
        yield Horizontal(
            Label("Backend URL (proxy): "),
            Input(placeholder="http://127.0.0.1:8080", id="nginx_backend", value="http://127.0.0.1:8080"),
            id="row_backend",
            classes="input-row"
        )

        yield Horizontal(
            Label("Root Path (static): "),
            Input(placeholder="/var/www/html", id="nginx_root", value="/var/www/html"),
            id="row_root",
            classes="input-row"
        )

        yield Horizontal(
            Label("Upstreams (lb, comma-sep): "),
            Input(placeholder="10.0.0.1:80, 10.0.0.2:80", id="nginx_upstreams", value="10.0.0.1:80, 10.0.0.2:80"),
            id="row_upstreams",
            classes="input-row"
        )

        yield Button("Generate", id="btn_generate_nginx", variant="primary")

        yield Label("Generated Configuration:")
        self.output_area = TextArea(id="nginx_output", read_only=False)
        self.output_area.disabled = True
        yield self.output_area

    def on_mount(self) -> None:
        self.update_visibility()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "nginx_type":
            self.update_visibility()

    def update_visibility(self) -> None:
        type_val = self.query_one("#nginx_type", Select).value

        row_backend = self.query_one("#row_backend")
        row_root = self.query_one("#row_root")
        row_upstreams = self.query_one("#row_upstreams")
        server_name = self.query_one("#nginx_server_name")

        if type_val == "proxy":
            row_backend.display = True
            row_root.display = False
            row_upstreams.display = False
            server_name.disabled = False
        elif type_val == "static":
            row_backend.display = False
            row_root.display = True
            row_upstreams.display = False
            server_name.disabled = False
        elif type_val == "loadbalancer":
            row_backend.display = False
            row_root.display = False
            row_upstreams.display = True
            server_name.disabled = True  # Load balancer config snippet doesn't use server_name in the generated block

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_generate_nginx":
            self.generate_config()

    def generate_config(self) -> None:
        type_val = self.query_one("#nginx_type", Select).value
        server_name = self.query_one("#nginx_server_name", Input).value
        port_str = self.query_one("#nginx_port", Input).value

        try:
            port = int(port_str) if port_str else 80
        except ValueError:
            self.app.notify("Invalid port number", severity="error")
            return

        config = ""
        if type_val == "proxy":
            backend = self.query_one("#nginx_backend", Input).value
            if not backend:
                self.app.notify("Backend URL required", severity="error")
                return
            config = self.manager.generate_proxy(server_name, backend, port)
        elif type_val == "static":
            root = self.query_one("#nginx_root", Input).value
            if not root:
                self.app.notify("Root path required", severity="error")
                return
            config = self.manager.generate_static(server_name, root, port)
        elif type_val == "loadbalancer":
            upstreams_str = self.query_one("#nginx_upstreams", Input).value
            if not upstreams_str:
                self.app.notify("Upstreams required", severity="error")
                return
            upstreams = [u.strip() for u in upstreams_str.split(",") if u.strip()]
            config = self.manager.generate_loadbalancer(upstreams, port)

        self.output_area.text = config
