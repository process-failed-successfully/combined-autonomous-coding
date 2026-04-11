from textual.app import ComposeResult
from textual.widgets import TextArea, Button, Static, Label, Select, Input
from textual.containers import Vertical, Horizontal, Container

from shared.sri_lab import SriManager


class SriLabTab(Container):
    """A Textual tab for computing SRI hashes and HTML tags."""

    def __init__(self, project_dir=None):
        super().__init__(id="tab-sri")
        self.manager = SriManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-1"):
            yield Static("Subresource Integrity (SRI) Generator", classes="header mb-1 text-bold")

            with Horizontal(classes="h-auto border-b border-primary pb-1 mb-1"):
                with Vertical(classes="w-2-3 pr-1"):
                    yield Label("Source (URL or local file path):", classes="mb-1")
                    yield Input(placeholder="https://code.jquery.com/jquery-3.6.0.min.js", id="sri_source_input")

                with Vertical(classes="w-1-3"):
                    yield Label("Algorithm:", classes="mb-1")
                    yield Select(
                        [("SHA-384 (Recommended)", "sha384"), ("SHA-256", "sha256"), ("SHA-512", "sha512")],
                        value="sha384",
                        id="sri_algo_select",
                    )

            with Horizontal(classes="h-auto pb-1 mb-1"):
                yield Button("Generate SRI", id="btn_sri_generate", variant="primary", classes="mr-1")
                yield Button("Clear", id="btn_sri_clear", variant="error")

            with Vertical(classes="h-full mt-1 border-t border-primary pt-1"):
                yield Label("Integrity Hash:", classes="text-bold mb-1")
                self.hash_output = Input(id="sri_hash_output", classes="mb-2")
                # Workaround for textual versions where Input might not support read_only in __init__
                # Usually it's read_only=True on TextArea or we just restrict.
                yield self.hash_output

                yield Label("HTML Tag:", classes="text-bold mb-1")
                self.tag_output = TextArea(id="sri_tag_output", read_only=True, classes="h-1-3 mb-2")
                yield self.tag_output

                yield Label("All Hashes:", classes="text-bold mb-1")
                self.all_hashes_output = TextArea(id="sri_all_hashes_output", read_only=True, classes="h-1-3")
                yield self.all_hashes_output

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn_sri_clear":
            self.query_one("#sri_source_input", Input).value = ""
            self.hash_output.value = ""
            self.tag_output.text = ""
            self.all_hashes_output.text = ""
            return

        if button_id == "btn_sri_generate":
            source = self.query_one("#sri_source_input", Input).value.strip()
            if not source:
                self.app.notify("Source URL or file path cannot be empty.", severity="error")
                return

            algo_select = self.query_one("#sri_algo_select", Select).value
            if algo_select == Select.BLANK:
                algo = "sha384"
            else:
                algo = str(algo_select)

            try:
                # Disable button while fetching
                event.button.disabled = True

                # Doing it synchronously blocks the TUI but it's simpler for local/small fetch
                content = self.manager.fetch_content(source)
                hashes = self.manager.compute_hashes(content)

                integrity_hash = hashes[algo]
                html_tag = self.manager.generate_html_tag(source, integrity_hash)

                self.hash_output.value = integrity_hash
                self.tag_output.text = html_tag

                all_hashes_text = "\n".join([f"{a.upper()}: {h}" for a, h in hashes.items()])
                self.all_hashes_output.text = all_hashes_text

                self.app.notify("SRI hashes generated successfully.")
            except Exception as e:
                self.app.notify(f"Error: {e}", severity="error")
                self.hash_output.value = ""
                self.tag_output.text = ""
                self.all_hashes_output.text = ""
            finally:
                event.button.disabled = False
