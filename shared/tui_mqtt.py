from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, RichLog, Select, ListView, ListItem
from textual.containers import Container, Horizontal, Vertical
from shared.mqtt_lab import MqttLabManager


class MqttLabTab(Container):
    """
    Interactive MQTT Lab Tab.
    """
    def __init__(self, project_dir: Path = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = MqttLabManager()
        self.manager.on_message_callback = self.on_mqtt_message
        self.subscribed_topics = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]MQTT Lab[/bold]", classes="welcome-text")

            # Connection Settings
            with Horizontal(classes="stat-box", id="mqtt-conn-box"):
                with Vertical():
                    yield Label("Host:")
                    yield Input(placeholder="localhost", id="mqtt-host", value="localhost")
                with Vertical():
                    yield Label("Port:")
                    yield Input(placeholder="1883", id="mqtt-port", value="1883", type="integer")
                with Vertical():
                    yield Label("Client ID (opt):")
                    yield Input(placeholder="client-id", id="mqtt-client-id")
                with Vertical():
                    yield Label("User (opt):")
                    yield Input(placeholder="username", id="mqtt-user")
                with Vertical():
                    yield Label("Pass (opt):")
                    yield Input(placeholder="password", id="mqtt-pass", password=True)

                with Vertical():
                    yield Label("Action:")
                    yield Button("Connect", id="btn-mqtt-connect", variant="primary")
                    yield Button("Disconnect", id="btn-mqtt-disconnect", variant="error", disabled=True)

            with Horizontal():
                # Left Pane: Subscribe & Publish
                with Vertical(classes="stat-box", id="mqtt-left-pane"):
                    yield Label("[bold]Subscribe[/bold]")
                    with Horizontal():
                        yield Input(placeholder="Topic (e.g. sensors/#)", id="mqtt-sub-topic")
                        yield Select.from_values(["0", "1", "2"], id="mqtt-sub-qos", value="0")
                        yield Button("Sub", id="btn-mqtt-sub", variant="success", disabled=True)

                    yield Label("Subscriptions:")
                    yield ListView(id="mqtt-sub-list")

                    yield Label("[bold]Publish[/bold]")
                    yield Label("Topic:")
                    yield Input(placeholder="Topic...", id="mqtt-pub-topic")
                    yield Label("Message:")
                    yield Input(placeholder="Payload...", id="mqtt-pub-payload")
                    with Horizontal():
                        yield Select.from_values(["0", "1", "2"], id="mqtt-pub-qos", value="0")
                        yield Button("Publish", id="btn-mqtt-pub", variant="warning", disabled=True)

                # Right Pane: Messages
                with Vertical(classes="stat-box", id="mqtt-right-pane"):
                    with Horizontal():
                        yield Label("[bold]Message Log[/bold]")
                        yield Button("Clear", id="btn-mqtt-clear", variant="default")
                    yield RichLog(id="mqtt-log", wrap=True, highlight=True, markup=True)

    def on_mqtt_message(self, message: dict) -> None:
        """Callback for incoming messages."""
        # Must schedule update on main thread
        self.app.call_from_thread(self._update_log, message)

    def _update_log(self, message: dict) -> None:
        try:
            log = self.query_one("#mqtt-log", RichLog)

            timestamp = message.get("timestamp", 0)
            import datetime
            dt = datetime.datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")

            topic = message.get("topic", "")
            payload = message.get("payload", "")
            qos = message.get("qos", 0)
            retain = message.get("retain", False)

            retain_flag = "[dim]R[/dim]" if retain else ""

            log.write(f"[{dt}] [bold cyan]{topic}[/bold cyan] (Q{qos}{retain_flag}): {payload}")
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-mqtt-connect":
            await self.connect_broker()
        elif event.button.id == "btn-mqtt-disconnect":
            self.disconnect_broker()
        elif event.button.id == "btn-mqtt-sub":
            self.subscribe_topic()
        elif event.button.id == "btn-mqtt-pub":
            await self.publish_message()
        elif event.button.id == "btn-mqtt-clear":
            self.query_one("#mqtt-log", RichLog).clear()
            self.manager.clear_messages()

    async def connect_broker(self) -> None:
        if not self.manager.is_available():
            self.notify("paho-mqtt not installed.", severity="error")
            return

        host = self.query_one("#mqtt-host", Input).value
        port_str = self.query_one("#mqtt-port", Input).value
        port = int(port_str) if port_str.isdigit() else 1883
        client_id = self.query_one("#mqtt-client-id", Input).value
        user = self.query_one("#mqtt-user", Input).value
        password = self.query_one("#mqtt-pass", Input).value

        self.notify(f"Connecting to {host}:{port}...")
        self.query_one("#btn-mqtt-connect").disabled = True

        import asyncio
        success = await asyncio.to_thread(
            self.manager.connect, host, port, client_id, user, password
        )

        if success:
            self.notify("Connected to broker.")
            self.query_one("#btn-mqtt-disconnect").disabled = False
            self.query_one("#btn-mqtt-sub").disabled = False
            self.query_one("#btn-mqtt-pub").disabled = False
            # self.query_one("#mqtt-conn-box").disabled = True # Better not disable whole box, just inputs maybe?
        else:
            self.notify("Connection failed.", severity="error")
            self.query_one("#btn-mqtt-connect").disabled = False

    def disconnect_broker(self) -> None:
        self.manager.disconnect()
        self.notify("Disconnected.")
        self.query_one("#btn-mqtt-disconnect").disabled = True
        self.query_one("#btn-mqtt-connect").disabled = False
        self.query_one("#btn-mqtt-sub").disabled = True
        self.query_one("#btn-mqtt-pub").disabled = True

        # Clear subscriptions list in UI
        self.subscribed_topics = []
        self.query_one("#mqtt-sub-list", ListView).clear()

    def subscribe_topic(self) -> None:
        topic = self.query_one("#mqtt-sub-topic", Input).value
        if not topic:
            return

        qos = int(self.query_one("#mqtt-sub-qos", Select).value or 0)

        if self.manager.subscribe(topic, qos):
            self.notify(f"Subscribed to {topic}")
            if topic not in self.subscribed_topics:
                self.subscribed_topics.append(topic)
                self.query_one("#mqtt-sub-list", ListView).append(ListItem(Label(f"{topic} (Q{qos})")))
            self.query_one("#mqtt-sub-topic", Input).value = ""
        else:
            self.notify("Subscription failed.", severity="error")

    async def publish_message(self) -> None:
        topic = self.query_one("#mqtt-pub-topic", Input).value
        payload = self.query_one("#mqtt-pub-payload", Input).value
        if not topic:
            self.notify("Topic required.", severity="error")
            return

        qos = int(self.query_one("#mqtt-pub-qos", Select).value or 0)

        import asyncio
        success = await asyncio.to_thread(self.manager.publish, topic, payload, qos)

        if success:
            self.notify("Message published.")
        else:
            self.notify("Publish failed.", severity="error")
