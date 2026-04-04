import json

try:
    from textual.app import ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Label, TextArea
except ImportError:
    ComposeResult = None
    Horizontal = object
    Vertical = object
    Label = object
    TextArea = object

from shared.jsonpatch_lab import JsonPatchLabManager


class JsonPatchLabTab(Vertical):
    """TUI Tab for JSONPatch Lab."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = JsonPatchLabManager()

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="input-column", id="target-col"):
                yield Label("Target JSON:")
                # We do not use language="json" to avoid missing tree-sitter plugin errors
                ta1 = TextArea(id="input-target")
                try:
                    ta1.language = "json"
                except Exception:
                    pass
                yield ta1

            with Vertical(classes="input-column", id="patch-col"):
                yield Label("Patch JSON:")
                ta2 = TextArea(id="input-patch")
                try:
                    ta2.language = "json"
                except Exception:
                    pass
                yield ta2

        with Vertical(id="output-col"):
            yield Label("Resulting JSON:")
            ta3 = TextArea(id="output-result", read_only=True)
            try:
                ta3.language = "json"
            except Exception:
                pass
            yield ta3

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        target_ta = self.query_one("#input-target", TextArea)
        patch_ta = self.query_one("#input-patch", TextArea)
        output_ta = self.query_one("#output-result", TextArea)

        if event.text_area in (target_ta, patch_ta):
            target_text = target_ta.text.strip()
            patch_text = patch_ta.text.strip()

            if not target_text or not patch_text:
                output_ta.text = ""
                return

            try:
                result = self.manager.apply_patch(target_text, patch_text)
                output_ta.text = json.dumps(result, indent=2)
            except Exception as e:
                output_ta.text = f"Error: {e}"
