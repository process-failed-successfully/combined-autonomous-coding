from pathlib import Path
from typing import Optional, Any
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Tree, Input, Button, RichLog
from textual.widgets.tree import TreeNode
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.xml_lab import XmlLabManager
import xml.etree.ElementTree as ET
import json


class XmlLabTab(Container):
    """
    Interactive XML Lab Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = XmlLabManager()
        self.current_file: Optional[Path] = None
        self.root: Optional[ET.Element] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="xml-sidebar", classes="stat-box"):
                yield Label("[bold]XML Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="xml-file-tree")

            # Center: XML Tree
            with Vertical(id="xml-main", classes="stat-box"):
                yield Label("[bold]Structure[/bold]", id="lbl-xml-structure")
                yield Tree("Root", id="xml-tree")

            # Right: Actions & Output
            with Vertical(id="xml-actions-pane", classes="stat-box"):
                yield Label("[bold]Actions[/bold]")

                with Horizontal():
                    yield Button("Format", id="btn-xml-format", variant="primary", disabled=True)
                    yield Button("Validate", id="btn-xml-validate", variant="success", disabled=True)
                    yield Button("To JSON", id="btn-xml-json", variant="warning", disabled=True)

                yield Label("XPath Query:")
                yield Input(placeholder="//tag[@attr='val']", id="xml-xpath-input")
                yield Button("Run XPath", id="btn-xml-xpath", variant="default", disabled=True)

                yield Label("Edit Value (updates via XPath):")
                yield Input(placeholder="New Value", id="xml-value-input")
                yield Input(placeholder="Attribute (optional)", id="xml-attr-input")
                yield Button("Apply Edit", id="btn-xml-edit", variant="error", disabled=True)

                yield Label("Save Changes:")
                yield Button("Save File", id="btn-xml-save", variant="warning", disabled=True)

                yield Label("[bold]Output / Log[/bold]")
                yield RichLog(id="xml-log", wrap=True, highlight=True, markup=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.suffix.lower() == ".xml":
            self.load_file(path)
        else:
            self.notify("Please select a .xml file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        try:
            self.root = self.manager.load_file(str(path))
            self.build_tree()
            self.query_one("#lbl-xml-structure", Label).update(f"[bold]Structure: {path.name}[/bold]")

            # Enable buttons
            self.query_one("#btn-xml-format").disabled = False
            self.query_one("#btn-xml-validate").disabled = False
            self.query_one("#btn-xml-json").disabled = False
            self.query_one("#btn-xml-xpath").disabled = False
            self.query_one("#btn-xml-edit").disabled = False
            self.query_one("#btn-xml-save").disabled = False

            self.log_message(f"Loaded {path.name}")
        except Exception as e:
            self.log_message(f"[red]Error loading XML: {e}[/red]")
            self.root = None
            self.query_one("#xml-tree", Tree).clear()
            self._disable_buttons()

    def _disable_buttons(self) -> None:
        ids = ["#btn-xml-format", "#btn-xml-validate", "#btn-xml-json", "#btn-xml-xpath", "#btn-xml-edit", "#btn-xml-save"]
        for button_id in ids:
            try:
                self.query_one(button_id, Button).disabled = True
            except Exception:
                pass

    def build_tree(self) -> None:
        tree = self.query_one("#xml-tree", Tree)
        tree.clear()

        if self.root is None:
            return

        tree.root.set_label(self.root.tag)
        tree.root.data = self.root
        tree.root.expand()

        self._add_nodes(tree.root, self.root)

    def _add_nodes(self, parent_node: TreeNode[Any], element: ET.Element) -> None:
        for child in element:
            label = f"[bold]{child.tag}[/bold]"
            if child.text and child.text.strip():
                label += f": {child.text.strip()[:20]}"  # Truncate long text

            if child.attrib:
                label += f" {child.attrib}"

            node = parent_node.add(label, data=child, expand=False)
            self._add_nodes(node, child)

    @on(Button.Pressed, "#btn-xml-format")
    def on_format(self) -> None:
        if self.root is None:
            return
        try:
            formatted = self.manager.format(self.root)
            self.log_message("[bold]Formatted XML:[/bold]")
            # Escape formatting for RichLog markup
            self.log_message(formatted.replace("[", "\\["))
        except Exception as e:
            self.log_message(f"[red]Format Error: {e}[/red]")

    @on(Button.Pressed, "#btn-xml-validate")
    def on_validate(self) -> None:
        if self.root is None:
            return
        # Since we already parsed it into self.root, it is technically valid structure.
        # But we can re-validate textual content if we had the raw text.
        # Here we just confirm structure is valid in memory.
        self.log_message("[green]XML Structure is valid (parsed successfully).[/green]")

    @on(Button.Pressed, "#btn-xml-json")
    def on_to_json(self) -> None:
        if self.root is None:
            return
        try:
            data = {self.root.tag: self.manager.to_json(self.root)}
            json_str = json.dumps(data, indent=2)
            self.log_message("[bold]JSON Output:[/bold]")
            self.log_message(json_str)
        except Exception as e:
            self.log_message(f"[red]Conversion Error: {e}[/red]")

    @on(Button.Pressed, "#btn-xml-xpath")
    def on_xpath(self) -> None:
        if self.root is None:
            return
        query = self.query_one("#xml-xpath-input", Input).value
        if not query:
            self.log_message("[red]XPath query required.[/red]")
            return

        try:
            results = self.manager.xpath(self.root, query)
            self.log_message(f"[bold]XPath Results ({len(results)}):[/bold]")
            for item in results:
                if isinstance(item, ET.Element):
                    self.log_message(f"- <{item.tag}> {item.text or ''}")
                else:
                    self.log_message(f"- {item}")
        except Exception as e:
            self.log_message(f"[red]XPath Error: {e}[/red]")

    @on(Button.Pressed, "#btn-xml-edit")
    def on_edit(self) -> None:
        if self.root is None:
            return
        query = self.query_one("#xml-xpath-input", Input).value
        value = self.query_one("#xml-value-input", Input).value
        attr = self.query_one("#xml-attr-input", Input).value or None

        if not query:
            self.log_message("[red]XPath query required for edit.[/red]")
            return
        if value is None:  # Textual Input value is never None, but just in case
            # We allow empty string as value, so we don't check 'if not value'
            pass

        try:
            count = self.manager.edit(self.root, query, value, attr)
            self.log_message(f"[green]Modified {count} elements.[/green]")
            self.build_tree()  # Refresh tree
        except Exception as e:
            self.log_message(f"[red]Edit Error: {e}[/red]")

    @on(Button.Pressed, "#btn-xml-save")
    def on_save(self) -> None:
        if not self.current_file or self.root is None:
            return
        try:
            formatted = self.manager.format(self.root)
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(formatted)
            self.log_message(f"[green]Saved to {self.current_file.name}[/green]")
        except Exception as e:
            self.log_message(f"[red]Save Error: {e}[/red]")

    def log_message(self, message: str) -> None:
        log = self.query_one("#xml-log", RichLog)
        log.write(message)
