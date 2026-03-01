from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, TextArea, TabbedContent, TabPane
from shared.text_lab import TextLabManager


class TextLabTab(Container):
    """Tab for Text Manipulation (Case, Sort, Filter, etc.)."""

    DEFAULT_CSS = """
    TextLabTab {
        layout: vertical;
        height: 100%;
    }

    .text-pane {
        height: 1fr;
        border: solid $accent;
        margin: 1;
    }

    .control-pane {
        height: auto;
        min-height: 15;
        border: solid $secondary;
        margin: 1;
        padding: 1;
    }

    .stat-box {
        background: $boost;
        padding: 1;
        margin-bottom: 1;
    }

    Button {
        margin: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = TextLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Text Lab[/bold]", classes="welcome-text")

            # Input/Output Split
            with Horizontal(classes="text-pane"):
                with Vertical():
                    yield Label("Input")
                    yield TextArea(id="text-input")
                with Vertical():
                    yield Label("Output")
                    yield TextArea(id="text-output", read_only=False)

            # Controls
            with Container(classes="control-pane"):
                with TabbedContent():
                    with TabPane("Case"):
                        with Horizontal():
                            yield Button("Snake", id="btn-case-snake")
                            yield Button("Camel", id="btn-case-camel")
                            yield Button("Kebab", id="btn-case-kebab")
                            yield Button("Pascal", id="btn-case-pascal")
                            yield Button("Constant", id="btn-case-constant")
                        with Horizontal():
                            yield Button("Title", id="btn-case-title")
                            yield Button("Upper", id="btn-case-upper")
                            yield Button("Lower", id="btn-case-lower")
                            yield Button("Dot", id="btn-case-dot")
                            yield Button("Path", id="btn-case-path")

                    with TabPane("Lines"):
                        with Horizontal():
                            yield Button("Sort Asc", id="btn-line-sort")
                            yield Button("Sort Desc", id="btn-line-sort-desc")
                            yield Button("Unique", id="btn-line-unique")
                            yield Button("Reverse", id="btn-line-reverse")
                            yield Button("Shuffle", id="btn-line-shuffle")
                        with Horizontal():
                            yield Button("Number", id="btn-line-number")
                            yield Button("Trim", id="btn-line-trim")
                            yield Button("No Empty", id="btn-line-empty")
                            yield Button("1 Space", id="btn-line-space")

                    with TabPane("Filter"):
                        with Horizontal():
                            yield Input(placeholder="Regex Pattern...", id="text-filter-pattern")
                            yield Button("Keep Matches", id="btn-filter-keep", variant="primary")
                            yield Button("Remove Matches", id="btn-filter-remove", variant="error")

                    with TabPane("Hash"):
                        with Horizontal():
                            yield Button("MD5", id="btn-hash-md5")
                            yield Button("SHA1", id="btn-hash-sha1")
                            yield Button("SHA256", id="btn-hash-sha256")
                            yield Button("SHA512", id="btn-hash-sha512")

                    with TabPane("Stats"):
                        yield Button("Analyze", id="btn-text-stats", variant="primary")
                        yield Label("Stats will appear here...", id="lbl-text-stats")

            # Global Actions
            with Horizontal():
                yield Button("Swap Input/Output", id="btn-text-swap", variant="warning")
                yield Button("Clear", id="btn-text-clear", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if not btn_id:
            return

        if btn_id == "btn-text-swap":
            self.swap_content()
            return
        elif btn_id == "btn-text-clear":
            self.clear_content()
            return
        elif btn_id == "btn-text-stats":
            self.show_stats()
            return

        # Transformations
        text = self.query_one("#text-input", TextArea).text
        result = text  # Default

        try:
            # Case
            if btn_id == "btn-case-snake":
                result = self.manager.transform(text, "snake")
            elif btn_id == "btn-case-camel":
                result = self.manager.transform(text, "camel")
            elif btn_id == "btn-case-kebab":
                result = self.manager.transform(text, "kebab")
            elif btn_id == "btn-case-pascal":
                result = self.manager.transform(text, "pascal")
            elif btn_id == "btn-case-constant":
                result = self.manager.transform(text, "constant")
            elif btn_id == "btn-case-title":
                result = self.manager.transform(text, "title")
            elif btn_id == "btn-case-upper":
                result = self.manager.transform(text, "upper")
            elif btn_id == "btn-case-lower":
                result = self.manager.transform(text, "lower")
            elif btn_id == "btn-case-dot":
                result = self.manager.transform(text, "dot")
            elif btn_id == "btn-case-path":
                result = self.manager.transform(text, "path")

            # Lines
            elif btn_id == "btn-line-sort":
                result = self.manager.sort_lines(text)
            elif btn_id == "btn-line-sort-desc":
                result = self.manager.sort_lines(text, reverse=True)
            elif btn_id == "btn-line-unique":
                result = self.manager.unique_lines(text)
            elif btn_id == "btn-line-reverse":
                result = self.manager.reverse_lines(text)
            elif btn_id == "btn-line-shuffle":
                result = self.manager.shuffle_lines(text)
            elif btn_id == "btn-line-number":
                result = self.manager.number_lines(text)
            elif btn_id == "btn-line-trim":
                result = self.manager.trim_lines(text)
            elif btn_id == "btn-line-empty":
                result = self.manager.remove_empty_lines(text)
            elif btn_id == "btn-line-space":
                result = self.manager.collapse_spaces(text)

            # Filter
            elif btn_id in ["btn-filter-keep", "btn-filter-remove"]:
                pattern = self.query_one("#text-filter-pattern", Input).value
                exclude = (btn_id == "btn-filter-remove")
                result = self.manager.filter_lines(text, pattern, exclude=exclude)

            # Hash
            elif btn_id == "btn-hash-md5":
                result = self.manager.hash_text(text, "md5")
            elif btn_id == "btn-hash-sha1":
                result = self.manager.hash_text(text, "sha1")
            elif btn_id == "btn-hash-sha256":
                result = self.manager.hash_text(text, "sha256")
            elif btn_id == "btn-hash-sha512":
                result = self.manager.hash_text(text, "sha512")

            self.query_one("#text-output", TextArea).text = result

            if result.startswith("Error:"):
                self.notify("Operation failed.", severity="error")
            else:
                self.notify("Done.")

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#text-input", TextArea)
        output_area = self.query_one("#text-output", TextArea)
        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped.")

    def clear_content(self) -> None:
        self.query_one("#text-input", TextArea).text = ""
        self.query_one("#text-output", TextArea).text = ""
        self.notify("Cleared.")

    def show_stats(self) -> None:
        text = self.query_one("#text-input", TextArea).text
        stats = self.manager.analyze(text)

        lbl = self.query_one("#lbl-text-stats", Label)
        summary = (
            f"Length: {stats['length']} chars | "
            f"Lines: {stats['lines']} | "
            f"Words: {stats['words']} | "
            f"Non-space Chars: {stats['chars_no_space']}"
        )
        lbl.update(summary)
