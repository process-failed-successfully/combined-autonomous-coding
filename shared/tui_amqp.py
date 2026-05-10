import asyncio
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, Select
from textual.containers import Vertical, Horizontal
from textual import on

try:
    from shared.amqp_lab import AmqpLabManager
    AMQP_AVAILABLE = True
except ImportError:
    AMQP_AVAILABLE = False
    AmqpLabManager = None # type: ignore


class AmqpLabTab(Vertical):
    """
    AMQP (RabbitMQ) Lab Tab.
    Provides a UI to connect to an AMQP broker, publish, and consume messages.
    """

    def __init__(self, project_dir, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        if not AMQP_AVAILABLE:
            yield Label("[red]Error: pika library not found. Please install it using `pip install pika`.[/red]")
            return

        yield Label("[bold]AMQP / RabbitMQ Laboratory[/bold]", classes="welcome-text")

        with Vertical(classes="stat-box"):
            yield Label("Broker URL:")
            yield Input(value="amqp://guest:guest@localhost:5672/", id="amqp-url")

            with Horizontal():
                with Vertical():
                    yield Label("[bold]Publish[/bold]")
                    yield Label("Exchange:")
                    yield Input(placeholder="e.g. logs (leave blank for default)", id="pub-exchange")
                    yield Label("Routing Key / Queue:")
                    yield Input(placeholder="e.g. task_queue", id="pub-routing-key")
                    yield Label("Message:")
                    yield Input(placeholder="Message body", id="pub-body")
                    yield Button("Publish", id="btn-publish", variant="success")

                with Vertical():
                    yield Label("[bold]Consume[/bold]")
                    yield Label("Queue Name:")
                    yield Input(placeholder="e.g. task_queue", id="cons-queue")
                    yield Label("Message Limit (0 = all currently available):")
                    yield Input(value="0", type="integer", id="cons-limit")
                    yield Button("Consume (Get)", id="btn-consume", variant="primary")

        yield Label("[bold]Log[/bold]")
        yield RichLog(id="amqp-log", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-publish")
    async def handle_publish(self, event: Button.Pressed) -> None:
        if not AMQP_AVAILABLE:
            return

        url = self.query_one("#amqp-url", Input).value.strip()
        exchange = self.query_one("#pub-exchange", Input).value.strip()
        routing_key = self.query_one("#pub-routing-key", Input).value.strip()
        body = self.query_one("#pub-body", Input).value.strip()

        log = self.query_one("#amqp-log", RichLog)

        if not body:
            self.notify("Message body required", severity="error")
            return

        if not exchange and not routing_key:
            self.notify("Exchange or Routing Key required", severity="error")
            return

        manager = AmqpLabManager(url=url)
        if not manager.is_available():
            log.write("[red]pika is not installed.[/red]")
            return

        log.write(f"Publishing to exchange '{exchange}' with routing key '{routing_key}'...")

        # Run in thread
        success = await asyncio.to_thread(manager.publish, exchange, routing_key, body)
        if success:
            log.write("[green]✅ Message published successfully.[/green]")
        else:
            log.write("[red]❌ Failed to publish message. Check broker URL and connection.[/red]")

    @on(Button.Pressed, "#btn-consume")
    async def handle_consume(self, event: Button.Pressed) -> None:
        if not AMQP_AVAILABLE:
            return

        url = self.query_one("#amqp-url", Input).value.strip()
        queue = self.query_one("#cons-queue", Input).value.strip()
        limit_str = self.query_one("#cons-limit", Input).value.strip()

        log = self.query_one("#amqp-log", RichLog)

        if not queue:
            self.notify("Queue name required for consuming", severity="error")
            return

        try:
            limit = int(limit_str) if limit_str else 0
        except ValueError:
            limit = 0

        manager = AmqpLabManager(url=url)
        if not manager.is_available():
            log.write("[red]pika is not installed.[/red]")
            return

        log.write(f"Attempting to basic_get messages from queue '{queue}'...")

        def _do_consume():
            return list(manager.consume_messages(queue, limit=limit))

        messages = await asyncio.to_thread(_do_consume)

        if not messages:
            log.write("[yellow]No messages available in the queue right now.[/yellow]")
        else:
            for i, msg in enumerate(messages):
                log.write(f"[cyan]Message {i+1}:[/cyan]")
                log.write(f"  Exchange: {msg['exchange']}")
                log.write(f"  Routing Key: {msg['routing_key']}")
                log.write(f"  Body: {msg['body']}")
            log.write(f"[green]✅ Retrieved {len(messages)} messages.[/green]")
