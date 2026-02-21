import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, TextArea, Select, TabbedContent, TabPane, RichLog
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.converter_lab import ConverterManager
from shared.ask import run_ask_logic
import io
import contextlib

class ConverterLabTab(Container):
    """
    Tab for code and format conversions.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ConverterManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Code & Format Converter[/bold]", classes="welcome-text")

            with TabbedContent(id="tabs"):
                # Tab 1: CURL to Code
                with TabPane("CURL -> Code", id="tab-curl"):
                    with Horizontal(classes="stat-box"):
                        yield Select.from_values(["Python (Requests)", "Node.js (Fetch)"], id="curl-target", value="Python (Requests)", allow_blank=False)
                        yield Button("Convert", id="btn-curl-convert", variant="primary")
                        yield Button("Clear", id="btn-curl-clear", variant="error")
                        yield Button("Ask AI (Fallback)", id="btn-curl-ai", variant="warning")

                    with Horizontal():
                        with Vertical(classes="stat-box"):
                            yield Label("CURL Command:")
                            yield TextArea(id="curl-input")

                        with Vertical(classes="stat-box"):
                            yield Label("Generated Code:")
                            yield TextArea(id="curl-output", read_only=True, language="python")

                # Tab 2: JSON to Types
                with TabPane("JSON -> Types", id="tab-types"):
                    with Horizontal(classes="stat-box"):
                        yield Select.from_values(["Pydantic (Python)", "TypeScript Interface"], id="type-target", value="Pydantic (Python)", allow_blank=False)
                        yield Button("Convert", id="btn-type-convert", variant="primary")
                        yield Button("Clear", id="btn-type-clear", variant="error")

                    with Horizontal():
                        with Vertical(classes="stat-box"):
                            yield Label("JSON Input:")
                            yield TextArea(id="type-input", language="json")

                        with Vertical(classes="stat-box"):
                            yield Label("Generated Types:")
                            yield TextArea(id="type-output", read_only=True, language="python")

                # Tab 3: Format Converter
                with TabPane("Format Converter", id="tab-format"):
                    with Horizontal(classes="stat-box"):
                        yield Label("From:")
                        yield Select.from_values(["JSON", "YAML", "TOML", "XML"], id="fmt-from", value="JSON", allow_blank=False)
                        yield Label("To:")
                        yield Select.from_values(["JSON", "YAML", "TOML", "XML"], id="fmt-to", value="YAML", allow_blank=False)
                        yield Button("Convert", id="btn-fmt-convert", variant="primary")
                        yield Button("Swap", id="btn-fmt-swap", variant="default")

                    with Horizontal():
                        with Vertical(classes="stat-box"):
                            yield Label("Input:")
                            yield TextArea(id="fmt-input")

                        with Vertical(classes="stat-box"):
                            yield Label("Output:")
                            yield TextArea(id="fmt-output", read_only=True)

    @on(Button.Pressed, "#btn-curl-convert")
    def on_curl_convert(self) -> None:
        cmd = self.query_one("#curl-input", TextArea).text
        target = self.query_one("#curl-target", Select).value

        output_area = self.query_one("#curl-output", TextArea)

        if not cmd.strip():
            self.notify("Input required.", severity="error")
            return

        target_str = str(target) if target is not None else ""

        try:
            if "Python" in target_str:
                output_area.language = "python"
                result = self.manager.curl_to_python(cmd)
            else:
                output_area.language = "javascript"
                result = self.manager.curl_to_node(cmd)

            output_area.text = result
            self.notify("Conversion complete.")
        except Exception as e:
            output_area.text = f"# Error: {e}"
            self.notify("Conversion failed.", severity="error")

    @on(Button.Pressed, "#btn-curl-clear")
    def on_curl_clear(self) -> None:
        self.query_one("#curl-input", TextArea).text = ""
        self.query_one("#curl-output", TextArea).text = ""

    @on(Button.Pressed, "#btn-curl-ai")
    async def on_curl_ai(self) -> None:
        cmd = self.query_one("#curl-input", TextArea).text
        target = self.query_one("#curl-target", Select).value
        output_area = self.query_one("#curl-output", TextArea)

        if not cmd.strip():
            self.notify("Input required.", severity="error")
            return

        self.notify("Asking AI to convert... (please wait)")
        output_area.text = "# Thinking..."

        target_str = str(target) if target is not None else ""
        target_lang = "Python requests" if "Python" in target_str else "Node.js fetch"
        prompt = f"Convert this CURL command to {target_lang}. Provide ONLY the code.\n\n{cmd}"

        # Run AI
        output_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(output_capture):
                await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type="gemini", # Default
                    verbose=False
                )
            output_area.text = output_capture.getvalue()
            self.notify("AI Conversion complete.")
        except Exception as e:
            output_area.text = f"# AI Error: {e}"
            self.notify("AI failed.", severity="error")

    @on(Button.Pressed, "#btn-type-convert")
    def on_type_convert(self) -> None:
        inp = self.query_one("#type-input", TextArea).text
        target = self.query_one("#type-target", Select).value
        output_area = self.query_one("#type-output", TextArea)

        if not inp.strip():
            self.notify("Input required.", severity="error")
            return

        target_str = str(target) if target is not None else ""

        try:
            if "Pydantic" in target_str:
                output_area.language = "python"
                result = self.manager.json_to_pydantic(inp, "RootModel")
            else:
                output_area.language = "typescript"
                result = self.manager.json_to_typescript(inp, "RootInterface")

            output_area.text = result
            self.notify("Conversion complete.")
        except Exception as e:
            output_area.text = f"# Error: {e}"
            self.notify("Conversion failed.", severity="error")

    @on(Button.Pressed, "#btn-type-clear")
    def on_type_clear(self) -> None:
        self.query_one("#type-input", TextArea).text = ""
        self.query_one("#type-output", TextArea).text = ""

    @on(Button.Pressed, "#btn-fmt-convert")
    def on_fmt_convert(self) -> None:
        inp = self.query_one("#fmt-input", TextArea).text
        from_fmt = self.query_one("#fmt-from", Select).value
        to_fmt = self.query_one("#fmt-to", Select).value
        output_area = self.query_one("#fmt-output", TextArea)

        if not inp.strip():
            self.notify("Input required.", severity="error")
            return

        from_fmt_str = str(from_fmt) if from_fmt is not None else "JSON"
        to_fmt_str = str(to_fmt) if to_fmt is not None else "YAML"

        try:
            # Set syntax highlighting
            lang_map = {"JSON": "json", "YAML": "yaml", "TOML": "toml", "XML": "xml"}
            output_area.language = lang_map.get(to_fmt_str, None)

            result = self.manager.convert_format(inp, from_fmt_str, to_fmt_str)
            output_area.text = result
            self.notify("Conversion complete.")
        except Exception as e:
            output_area.text = f"# Error: {e}"
            self.notify(f"Conversion failed: {e}", severity="error")

    @on(Button.Pressed, "#btn-fmt-swap")
    def on_fmt_swap(self) -> None:
        s_from = self.query_one("#fmt-from", Select)
        s_to = self.query_one("#fmt-to", Select)

        val_from = s_from.value
        val_to = s_to.value

        s_from.value = val_to
        s_to.value = val_from

        # Swap content
        t_in = self.query_one("#fmt-input", TextArea)
        t_out = self.query_one("#fmt-output", TextArea)

        txt_in = t_in.text
        txt_out = t_out.text

        t_in.text = txt_out
        t_out.text = txt_in
