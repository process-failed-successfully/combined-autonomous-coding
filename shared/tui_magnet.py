import os
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Button, Input, Label, Static, TextArea
from shared.magnet_lab import MagnetLabManager

class MagnetLabTab(Container):
    """Tab for Magnet URI Encoding/Decoding."""

    DEFAULT_CSS = """
    MagnetLabTab {
        layout: vertical;
        height: 100%;
        padding: 1;
    }

    .magnet-section {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }

    .magnet-section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    .input-row {
        height: auto;
        margin-bottom: 1;
    }

    .input-row Input {
        width: 1fr;
    }

    .button-row {
        height: auto;
        margin-top: 1;
    }

    #magnet-output {
        height: 10;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Label("[bold]Magnet URI Lab[/bold]", classes="welcome-text")

            # Parse Section
            with Vertical(classes="magnet-section"):
                yield Label("Parse Magnet URI", classes="magnet-section-title")
                with Horizontal(classes="input-row"):
                    yield Input(placeholder="magnet:?xt=urn:btih:...", id="input-parse-uri")
                with Horizontal(classes="button-row"):
                    yield Button("Parse", id="btn-parse", variant="primary")

            # Build Section
            with Vertical(classes="magnet-section"):
                yield Label("Build Magnet URI", classes="magnet-section-title")
                with Horizontal(classes="input-row"):
                    yield Label("Info Hash: ", classes="input-label")
                    yield Input(placeholder="40-char hex string", id="input-build-hash")
                with Horizontal(classes="input-row"):
                    yield Label("Name (dn): ", classes="input-label")
                    yield Input(placeholder="Optional display name", id="input-build-name")
                with Horizontal(classes="input-row"):
                    yield Label("Trackers:  ", classes="input-label")
                    yield Input(placeholder="Comma-separated URLs", id="input-build-trackers")
                with Horizontal(classes="button-row"):
                    yield Button("Build", id="btn-build", variant="primary")

            # From Torrent Section
            with Vertical(classes="magnet-section"):
                yield Label("From .torrent File", classes="magnet-section-title")
                with Horizontal(classes="input-row"):
                    yield Input(placeholder="/path/to/file.torrent", id="input-torrent-path")
                with Horizontal(classes="button-row"):
                    yield Button("Generate", id="btn-torrent", variant="primary")

            # Output Section
            with Vertical(classes="magnet-section"):
                yield Label("Output", classes="magnet-section-title")
                yield TextArea(id="magnet-output", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        manager = MagnetLabManager()
        output_area = self.query_one("#magnet-output", TextArea)

        if event.button.id == "btn-parse":
            uri = self.query_one("#input-parse-uri", Input).value.strip()
            if not uri:
                self.notify("Please enter a Magnet URI to parse.", severity="warning")
                return

            result = manager.parse(uri)
            if result["success"]:
                import json
                output_area.text = json.dumps(result["result"], indent=2)
                self.notify("Parsed successfully.")
            else:
                output_area.text = f"Error: {result['error']}"
                self.notify("Parse failed.", severity="error")

        elif event.button.id == "btn-build":
            info_hash = self.query_one("#input-build-hash", Input).value.strip()
            if not info_hash:
                self.notify("Info Hash is required to build a Magnet URI.", severity="warning")
                return

            name = self.query_one("#input-build-name", Input).value.strip()
            trackers_str = self.query_one("#input-build-trackers", Input).value.strip()
            trackers = [t.strip() for t in trackers_str.split(",")] if trackers_str else []

            result = manager.build(info_hash, name, trackers)
            if result["success"]:
                output_area.text = result["uri"]
                self.notify("Built successfully.")
            else:
                output_area.text = f"Error: {result['error']}"
                self.notify("Build failed.", severity="error")

        elif event.button.id == "btn-torrent":
            path = self.query_one("#input-torrent-path", Input).value.strip()
            if not path:
                self.notify("Please enter a path to a .torrent file.", severity="warning")
                return

            result = manager.from_torrent(path)
            if result["success"]:
                output_area.text = result["uri"]
                self.notify("Generated successfully.")
            else:
                output_area.text = f"Error: {result['error']}"
                self.notify("Generation failed.", severity="error")
