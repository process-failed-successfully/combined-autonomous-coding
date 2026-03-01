from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, TextArea, TabbedContent, TabPane, Select
from shared.random_lab import RandomLabManager


class RandomLabTab(Container):
    """Tab for Random Lab (Integers, Floats, Strings, Choice, etc.)."""

    DEFAULT_CSS = """
    RandomLabTab {
        layout: vertical;
        height: 100%;
    }

    .pane {
        border: solid $accent;
        margin: 1;
        padding: 1;
        height: auto;
    }

    .output-pane {
        border: solid $secondary;
        margin: 1;
        padding: 1;
        height: 1fr;
    }

    .input-row {
        height: auto;
        align: left middle;
        margin-bottom: 1;
    }

    .input-row Input {
        width: 20;
        margin-right: 1;
    }

    Button {
        margin: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = RandomLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Random Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Numbers", id="pane-numbers"):
                    with Container(classes="pane"):
                        with Horizontal(classes="input-row"):
                            yield Label("Min:", classes="lbl")
                            yield Input(id="num-min", value="1")
                            yield Label("Max:", classes="lbl")
                            yield Input(id="num-max", value="100")
                            yield Label("Count:", classes="lbl")
                            yield Input(id="num-count", value="1")
                        with Horizontal():
                            yield Button("Generate Integer", id="btn-num-int", variant="primary")
                            yield Button("Generate Float", id="btn-num-float", variant="primary")

                with TabPane("Strings", id="pane-strings"):
                    with Container(classes="pane"):
                        with Horizontal(classes="input-row"):
                            yield Label("Length:", classes="lbl")
                            yield Input(id="str-length", value="10")
                            yield Label("Count:", classes="lbl")
                            yield Input(id="str-count", value="1")
                        with Horizontal(classes="input-row"):
                            yield Label("Charset:", classes="lbl")
                            yield Select(
                                [
                                    ("Alphanumeric (alnum)", "alnum"),
                                    ("Alphabetic (alpha)", "alpha"),
                                    ("Numeric (numeric)", "numeric"),
                                    ("Hexadecimal (hex)", "hex"),
                                    ("Special (special)", "special"),
                                    ("All (all)", "all")
                                ],
                                id="str-charset",
                                value="alnum"
                            )
                            yield Label("Custom:", classes="lbl")
                            yield Input(id="str-custom-charset", placeholder="Optional custom charset")
                        with Horizontal():
                            yield Button("Generate String", id="btn-str-generate", variant="primary")

                with TabPane("UUIDs", id="pane-uuids"):
                    with Container(classes="pane"):
                        with Horizontal(classes="input-row"):
                            yield Label("Version:", classes="lbl")
                            yield Select(
                                [("v4 (Random)", "4"), ("v1 (Time-based)", "1")],
                                id="uuid-version",
                                value="4"
                            )
                            yield Label("Count:", classes="lbl")
                            yield Input(id="uuid-count", value="1")
                        with Horizontal():
                            yield Button("Generate UUID", id="btn-uuid-generate", variant="primary")

                with TabPane("Fun", id="pane-fun"):
                    with Container(classes="pane"):
                        with Horizontal(classes="input-row"):
                            yield Label("Count:", classes="lbl")
                            yield Input(id="fun-count", value="1")
                            yield Label("Dice Sides:", classes="lbl")
                            yield Input(id="fun-sides", value="6")
                        with Horizontal():
                            yield Button("Flip Coin", id="btn-fun-coin", variant="primary")
                            yield Button("Roll Dice", id="btn-fun-dice", variant="primary")

                with TabPane("Choice & Lines", id="pane-choice"):
                    with Container(classes="pane"):
                        yield Label("Items (comma separated) or Text Lines:")
                        yield TextArea(id="choice-input", text="Apple, Banana, Cherry")
                        with Horizontal(classes="input-row"):
                            yield Label("Count:", classes="lbl")
                            yield Input(id="choice-count", value="1")
                        with Horizontal():
                            yield Button("Choice (Comma list)", id="btn-choice-items", variant="primary")
                            yield Button("Pick Lines", id="btn-choice-pick", variant="primary")
                            yield Button("Shuffle Lines", id="btn-choice-shuffle", variant="primary")

            with Container(classes="output-pane"):
                with Horizontal():
                    yield Label("[bold]Output:[/bold]")
                    yield Button("Clear Output", id="btn-clear-output", variant="error")
                yield TextArea(id="random-output", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if not btn_id:
            return

        if btn_id == "btn-clear-output":
            self.query_one("#random-output", TextArea).text = ""
            return

        output_area = self.query_one("#random-output", TextArea)
        results = []

        try:
            if btn_id in ("btn-num-int", "btn-num-float"):
                min_val = float(self.query_one("#num-min", Input).value or 0)
                max_val = float(self.query_one("#num-max", Input).value or 100)
                count = int(self.query_one("#num-count", Input).value or 1)

                if btn_id == "btn-num-int":
                    results = [str(x) for x in self.manager.generate_int(int(min_val), int(max_val), count)]
                else:
                    results = [str(x) for x in self.manager.generate_float(min_val, max_val, count)]

            elif btn_id == "btn-str-generate":
                length = int(self.query_one("#str-length", Input).value or 10)
                count = int(self.query_one("#str-count", Input).value or 1)
                custom_charset = self.query_one("#str-custom-charset", Input).value
                charset = custom_charset if custom_charset else self.query_one("#str-charset", Select).value
                if not charset:
                    charset = "alnum"

                results = self.manager.generate_string(length, charset, count)

            elif btn_id == "btn-uuid-generate":
                version = int(self.query_one("#uuid-version", Select).value or 4)
                count = int(self.query_one("#uuid-count", Input).value or 1)
                results = self.manager.generate_uuid(version, count)

            elif btn_id == "btn-fun-coin":
                count = int(self.query_one("#fun-count", Input).value or 1)
                results = self.manager.flip_coin(count)

            elif btn_id == "btn-fun-dice":
                count = int(self.query_one("#fun-count", Input).value or 1)
                sides = int(self.query_one("#fun-sides", Input).value or 6)
                results = [str(x) for x in self.manager.roll_dice(sides, count)]

            elif btn_id == "btn-choice-items":
                count = int(self.query_one("#choice-count", Input).value or 1)
                input_text = self.query_one("#choice-input", TextArea).text
                items = [x.strip() for x in input_text.split(",") if x.strip()]
                results = self.manager.choice(items, count)

            elif btn_id == "btn-choice-pick":
                # Write to temp file to use manager.pick_lines (or just rewrite the logic here)
                count = int(self.query_one("#choice-count", Input).value or 1)
                input_text = self.query_one("#choice-input", TextArea).text
                lines = [x for x in input_text.splitlines() if x.strip()]
                if not lines:
                    raise ValueError("No lines to pick from.")
                import random
                rng = random.SystemRandom()
                results = [rng.choice(lines) for _ in range(count)]

            elif btn_id == "btn-choice-shuffle":
                input_text = self.query_one("#choice-input", TextArea).text
                lines = [x for x in input_text.splitlines() if x.strip()]
                if not lines:
                    raise ValueError("No lines to shuffle.")
                import random
                rng = random.SystemRandom()
                rng.shuffle(lines)
                results = lines

            if results:
                current_text = output_area.text
                new_text = "\n".join(results)
                output_area.text = f"{current_text}\n{new_text}".strip()
                self.notify("Generated.")

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
