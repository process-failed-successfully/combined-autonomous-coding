import asyncio
import json
from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, ListView, ListItem, TextArea, RichLog, Select, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual import on, work
from shared.kafka_lab import KafkaLabManager

class KafkaLabTab(Container):
    """
    Kafka Management Tab.
    Supports listing topics, producing, and consuming messages.
    """

    def __init__(self, project_dir: Path = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = KafkaLabManager()
        self.is_consuming = False
        self.stop_consuming_flag = False

    def compose(self) -> ComposeResult:
        if not self.manager.is_available():
            with Vertical(classes="stat-box"):
                yield Label("[bold red]Kafka Library Not Found[/bold red]")
                yield Label("Please install 'kafka-python' to use this feature:")
                yield Input(value="pip install kafka-python", disabled=True)
            return

        with Horizontal():
            # Left Pane: Topics
            with Vertical(id="kafka-sidebar", classes="stat-box"):
                yield Label("[bold]Topics[/bold]")
                yield ListView(id="kafka-topic-list")

                with Horizontal():
                    yield Input(placeholder="New Topic", id="kafka-new-topic-input")
                    yield Button("Create", id="btn-kafka-create", variant="primary")

                yield Button("Delete Selected", id="btn-kafka-delete", variant="error", disabled=True)
                yield Button("Refresh", id="btn-kafka-refresh", variant="default")

            # Right Pane: Actions
            with Vertical(id="kafka-main"):
                with TabbedContent():
                    with TabPane("Produce"):
                        with Vertical(classes="stat-box"):
                            yield Label("Target Topic:")
                            yield Label("None", id="lbl-kafka-target-topic", classes="value")

                            yield Label("Key (Optional):")
                            yield Input(placeholder="Message Key...", id="kafka-produce-key")

                            yield Label("Value:")
                            yield TextArea(id="kafka-produce-value")

                            yield Button("Send Message", id="btn-kafka-send", variant="success", disabled=True)
                            yield RichLog(id="kafka-produce-log", wrap=True, highlight=True, markup=True)

                    with TabPane("Consume"):
                        with Vertical(classes="stat-box"):
                            yield Label("Source Topic:")
                            yield Label("None", id="lbl-kafka-source-topic", classes="value")

                            with Horizontal():
                                yield Label("Group ID (Optional):")
                                yield Input(placeholder="my-group", id="kafka-group-id")

                            with Horizontal():
                                yield Button("Start Consuming", id="btn-kafka-consume-start", variant="primary", disabled=True)
                                yield Button("Stop", id="btn-kafka-consume-stop", variant="error", disabled=True)
                                yield Button("Clear Log", id="btn-kafka-clear-log", variant="default")

                            yield RichLog(id="kafka-consume-log", wrap=True, highlight=True, markup=True)

                    with TabPane("Brokers"):
                        with Vertical(classes="stat-box"):
                            yield Label("Bootstrap Servers (comma separated):")
                            yield Input(value="localhost:9092", id="kafka-brokers-input")
                            yield Button("Update Brokers", id="btn-kafka-update-brokers", variant="warning")
                            yield Label("Current: localhost:9092", id="lbl-kafka-brokers")

    def on_mount(self) -> None:
        if self.manager.is_available():
            self.refresh_topics()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-kafka-refresh":
            self.refresh_topics()
        elif event.button.id == "btn-kafka-create":
            await self.create_topic()
        elif event.button.id == "btn-kafka-delete":
            await self.delete_topic()
        elif event.button.id == "btn-kafka-send":
            await self.produce_message()
        elif event.button.id == "btn-kafka-consume-start":
            self.start_consuming()
        elif event.button.id == "btn-kafka-consume-stop":
            self.stop_consuming()
        elif event.button.id == "btn-kafka-clear-log":
            self.query_one("#kafka-consume-log", RichLog).clear()
        elif event.button.id == "btn-kafka-update-brokers":
            self.update_brokers()

    def update_brokers(self) -> None:
        brokers = self.query_one("#kafka-brokers-input", Input).value
        self.manager = KafkaLabManager(bootstrap_servers=brokers)
        self.query_one("#lbl-kafka-brokers", Label).update(f"Current: {brokers}")
        self.notify("Brokers updated.")
        self.refresh_topics()

    def refresh_topics(self) -> None:
        list_view = self.query_one("#kafka-topic-list", ListView)
        list_view.clear()

        # Run in thread
        import asyncio
        asyncio.create_task(self._async_refresh_topics())

    async def _async_refresh_topics(self) -> None:
        topics = await asyncio.to_thread(self.manager.list_topics)
        list_view = self.query_one("#kafka-topic-list", ListView)
        list_view.clear()

        if not topics:
            list_view.append(ListItem(Label("No topics found or connection failed")))
            return

        for t in topics:
            list_view.append(ListItem(Label(t), name=t))

        self.notify("Topics refreshed.")

    async def create_topic(self) -> None:
        topic = self.query_one("#kafka-new-topic-input", Input).value
        if not topic:
            self.notify("Topic name required.", severity="error")
            return

        success = await asyncio.to_thread(self.manager.create_topic, topic)
        if success:
            self.notify(f"Topic '{topic}' created.")
            self.query_one("#kafka-new-topic-input", Input).value = ""
            self.refresh_topics()
        else:
            self.notify("Failed to create topic.", severity="error")

    async def delete_topic(self) -> None:
        list_view = self.query_one("#kafka-topic-list", ListView)
        if list_view.index is None:
            return

        item = list_view.children[list_view.index]
        if not item.name: return
        topic = item.name

        success = await asyncio.to_thread(self.manager.delete_topic, topic)
        if success:
            self.notify(f"Topic '{topic}' deleted.")
            self.refresh_topics()

            # Reset selection if it matches
            target_lbl = self.query_one("#lbl-kafka-target-topic", Label)
            if str(target_lbl.render()) == topic:
                 target_lbl.update("None")
                 self.query_one("#btn-kafka-send").disabled = True

            source_lbl = self.query_one("#lbl-kafka-source-topic", Label)
            if str(source_lbl.render()) == topic:
                 source_lbl.update("None")
                 self.query_one("#btn-kafka-consume-start").disabled = True

        else:
            self.notify("Failed to delete topic.", severity="error")

    @on(ListView.Selected, "#kafka-topic-list")
    def on_topic_selected(self, event: ListView.Selected) -> None:
        if event.item and event.item.name:
            topic = event.item.name
            self.query_one("#btn-kafka-delete").disabled = False

            # Update targets
            self.query_one("#lbl-kafka-target-topic", Label).update(topic)
            self.query_one("#btn-kafka-send").disabled = False

            self.query_one("#lbl-kafka-source-topic", Label).update(topic)
            self.query_one("#btn-kafka-consume-start").disabled = False

    async def produce_message(self) -> None:
        topic = str(self.query_one("#lbl-kafka-target-topic", Label).render())
        if topic == "None": return

        key = self.query_one("#kafka-produce-key", Input).value
        value = self.query_one("#kafka-produce-value", TextArea).text

        if not value:
            self.notify("Message value required.", severity="error")
            return

        log = self.query_one("#kafka-produce-log", RichLog)

        success = await asyncio.to_thread(self.manager.produce, topic, value, key if key else None)

        if success:
            self.notify("Message sent.")
            log.write(f"[green]Sent to {topic}:[/green] {value[:50]}...")
            # Clear inputs? Maybe not, user might want to edit and resend.
        else:
            self.notify("Failed to send.", severity="error")
            log.write(f"[red]Failed to send to {topic}[/red]")

    def start_consuming(self) -> None:
        topic = str(self.query_one("#lbl-kafka-source-topic", Label).render())
        if topic == "None": return

        if self.is_consuming:
            return

        self.is_consuming = True
        self.stop_consuming_flag = False

        self.query_one("#btn-kafka-consume-start").disabled = True
        self.query_one("#btn-kafka-consume-stop").disabled = False

        group_id = self.query_one("#kafka-group-id", Input).value

        self.notify(f"Started consuming from {topic}...")
        self.run_consumer_thread(topic, group_id if group_id else None)

    @work(exclusive=True, thread=True)
    def run_consumer_thread(self, topic: str, group_id: Optional[str]) -> None:
        log = self.query_one("#kafka-consume-log", RichLog)

        try:
            # Infinite loop generator
            for msg in self.manager.consume_messages(topic, group_id=group_id, follow=True):
                if self.stop_consuming_flag:
                    break

                if msg is None:
                    continue

                # Format message
                key_str = f"[bold blue]Key: {msg['key']}[/bold blue] | " if msg['key'] else ""
                val_str = f"{msg['value']}"
                line = f"[{msg['partition']}:{msg['offset']}] {key_str}{val_str}"

                self.app.call_from_thread(log.write, line)
        except Exception as e:
            self.app.call_from_thread(log.write, f"[bold red]Error: {e}[/bold red]")
        finally:
            self.app.call_from_thread(self.on_consumer_stopped)

    def stop_consuming(self) -> None:
        self.stop_consuming_flag = True
        self.notify("Stopping consumer...")

    def on_consumer_stopped(self) -> None:
        self.is_consuming = False
        self.query_one("#btn-kafka-consume-start").disabled = False
        self.query_one("#btn-kafka-consume-stop").disabled = True
        self.notify("Consumer stopped.")
