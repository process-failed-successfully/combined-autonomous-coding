from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, TextArea, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.xml_lab import XmlLabManager
import json


class XmlLabTab(Container):
    """
    Interactive XML Lab Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = XmlLabManager()

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: XML Input
            with Vertical(id="xml-input-pane", classes="stat-box"):
                yield Label("[bold]Input XML[/bold]")
                yield TextArea(id="xml-input", language="xml")

            # Right: Controls & Output
            with Vertical(id="xml-controls-pane", classes="stat-box"):
                yield Label("[bold]Actions[/bold]")
                with Horizontal():
                    yield Button("Format", id="btn-xml-format", variant="primary")
                    yield Button("Validate", id="btn-xml-validate", variant="success")
                    yield Button("To JSON", id="btn-xml-json", variant="warning")

                yield Label("[bold]XPath Query[/bold]")
                with Horizontal():
                    yield Input(placeholder="//tag[@attr='val']", id="xml-xpath-input")
                    yield Button("Run", id="btn-xml-xpath-run", variant="default")

                yield Label("[bold]Output[/bold]")
                yield RichLog(id="xml-output", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-xml-format")
    def on_format(self) -> None:
        inp = self.query_one("#xml-input", TextArea)
        content = inp.text
        log = self.query_one("#xml-output", RichLog)
        log.clear()

        if not content.strip():
            log.write("[red]Input is empty.[/red]")
            return

        try:
            root = self.manager.parse(content)
            formatted = self.manager.format(root)
            inp.text = formatted
            log.write("[green]Formatted XML.[/green]")
        except Exception as e:
            log.write(f"[red]Error formatting XML: {e}[/red]")

    @on(Button.Pressed, "#btn-xml-validate")
    def on_validate(self) -> None:
        inp = self.query_one("#xml-input", TextArea)
        content = inp.text
        log = self.query_one("#xml-output", RichLog)
        log.clear()

        if not content.strip():
            log.write("[red]Input is empty.[/red]")
            return

        error = self.manager.validate(content)
        if error:
            log.write(f"[red]Invalid XML: {error}[/red]")
        else:
            log.write("[green]Valid XML.[/green]")

    @on(Button.Pressed, "#btn-xml-json")
    def on_to_json(self) -> None:
        inp = self.query_one("#xml-input", TextArea)
        content = inp.text
        log = self.query_one("#xml-output", RichLog)
        log.clear()

        if not content.strip():
            log.write("[red]Input is empty.[/red]")
            return

        try:
            root = self.manager.parse(content)
            data = self.manager.to_json(root)
            json_str = json.dumps(data, indent=2)
            log.write(json_str)
        except Exception as e:
            log.write(f"[red]Error converting to JSON: {e}[/red]")

    @on(Button.Pressed, "#btn-xml-xpath-run")
    def on_xpath(self) -> None:
        inp = self.query_one("#xml-input", TextArea)
        content = inp.text
        xpath_query = self.query_one("#xml-xpath-input", Input).value
        log = self.query_one("#xml-output", RichLog)
        log.clear()

        if not content.strip():
            log.write("[red]Input is empty.[/red]")
            return

        if not xpath_query:
            log.write("[red]XPath query is empty.[/red]")
            return

        try:
            root = self.manager.parse(content)
            results = self.manager.xpath(root, xpath_query)

            if not results:
                log.write("No matches found.")
            else:
                log.write(f"Found {len(results)} matches:")
                for i, item in enumerate(results):
                    # We can't easily print Element objects nicely without converting back to string
                    try:
                        # Re-use manager format logic on sub-elements?
                        # Or simple tostring
                        snippet = self.manager.format(item)
                        log.write(f"[bold]Match {i+1}:[/bold]\n{snippet}")
                    except Exception:
                        log.write(f"[bold]Match {i+1}:[/bold] {item}")

        except Exception as e:
            log.write(f"[red]Error executing XPath: {e}[/red]")
