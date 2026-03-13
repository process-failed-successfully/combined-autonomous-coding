from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.widgets import Button, Input, Select, Static, Label, TextArea
from pathlib import Path
import json

from shared.ocr_lab import OcrLabManager, HAS_OCR

class OcrLabTab(Container):
    """A Textual tab for the OCR Lab."""

    def __init__(self, project_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = OcrLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("OCR Lab", classes="header")

            if not HAS_OCR:
                yield Static("pytesseract or Pillow is not installed. Please install 'pytesseract' and 'Pillow'.", classes="error")
                return

            with Horizontal(classes="controls-row"):
                yield Input(placeholder="Path to image file...", id="ocr-file-input", classes="flex-1")
                # We'll populate this select dynamically later
                yield Select([], prompt="Select Language", id="ocr-lang-select", classes="flex-1")

            with Horizontal(classes="buttons-row"):
                yield Button("Extract Text", id="ocr-extract-btn", variant="primary")
                yield Button("Get Detailed Data", id="ocr-data-btn", variant="default")

            yield Static("Output:", classes="label")
            yield TextArea(id="ocr-output", read_only=True, classes="tall-text-area")

    async def on_mount(self):
        try:
            langs = self.manager.get_languages()
            select = self.query_one("#ocr-lang-select", Select)
            options = [(l, l) for l in langs]
            select.set_options(options)
            if "eng" in langs:
                select.value = "eng"
        except Exception as e:
            pass # Ignore errors, Tesseract might not be fully installed or configured

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id in ("ocr-extract-btn", "ocr-data-btn"):
            file_input = self.query_one("#ocr-file-input", Input).value.strip()

            # Select value could be None or Select.BLANK. If None or blank, use None.
            lang = None
            select = self.query_one("#ocr-lang-select", Select)
            if select.value and select.value != Select.BLANK:
                lang = select.value

            if not file_input:
                self._update_output("Error: Please specify an image file path.")
                return

            file_path = Path(file_input)
            if not file_path.is_absolute():
                file_path = self.project_dir / file_path

            if not file_path.exists():
                self._update_output(f"Error: File '{file_path}' does not exist.")
                return

            self._update_output("Processing...")
            if button_id == "ocr-extract-btn":
                self.run_worker(self._extract_text(file_path, lang), thread=True, exclusive=True)
            elif button_id == "ocr-data-btn":
                self.run_worker(self._get_data(file_path, lang), thread=True, exclusive=True)

    def _update_output(self, text: str):
        text_area = self.query_one("#ocr-output", TextArea)
        text_area.text = text

    def _extract_text(self, file_path: Path, lang: str):
        try:
            result = self.manager.extract_text(file_path, lang)
            self.app.call_from_thread(self._update_output, result or "No text found.")
        except Exception as e:
            self.app.call_from_thread(self._update_output, f"Error: {e}")

    def _get_data(self, file_path: Path, lang: str):
        try:
            result = self.manager.get_data(file_path, lang)
            self.app.call_from_thread(self._update_output, json.dumps(result, indent=2))
        except Exception as e:
            self.app.call_from_thread(self._update_output, f"Error: {e}")
