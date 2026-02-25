from pathlib import Path
from typing import List, Optional
import asyncio
import io
import contextlib

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, ListView, ListItem, RichLog, Input, TextArea, TabbedContent, TabPane, Select, Static
from textual import on
from rich.text import Text

from shared.knowledge import KnowledgeManager
from shared.ask import run_ask_logic

class KnowledgeGraphTab(Container):
    """
    Interactive Knowledge Graph Explorer.
    Allows searching, navigating relationships, and context-aware chat.
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = KnowledgeManager()
        self.selected_node_id: Optional[int] = None
        self.all_nodes_cache = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # --- Left Pane: Search & List ---
            with Vertical(id="kg-sidebar", classes="stat-box"):
                yield Label("[bold]Knowledge Graph[/bold]", classes="welcome-text")
                yield Input(placeholder="Search nodes...", id="kg-search-input")
                yield ListView(id="kg-node-list")
                with Horizontal():
                    yield Button("New Node", id="btn-kg-new", variant="primary")
                    yield Button("Refresh", id="btn-kg-refresh", variant="default")

            # --- Right Pane: Explorer ---
            with Vertical(id="kg-main"):
                # Header
                yield Label("Select a node to explore.", id="kg-header-lbl")

                with TabbedContent(id="kg-tabs"):
                    # --- Tab 1: Content & Edit ---
                    with TabPane("Content", id="tab-kg-content"):
                        yield TextArea(id="kg-content-editor", disabled=True)
                        with Horizontal(classes="stat-box"):
                            yield Button("Save Changes", id="btn-kg-save", variant="success", disabled=True)
                            yield Button("Delete Node", id="btn-kg-delete", variant="error", disabled=True)

                    # --- Tab 2: Relationships (Graph) ---
                    with TabPane("Relationships", id="tab-kg-links"):
                        with Horizontal():
                            # Incoming
                            with Vertical(classes="stat-box"):
                                yield Label("[bold]Incoming (Linked From)[/bold]")
                                yield ListView(id="kg-incoming-list")

                            # Outgoing
                            with Vertical(classes="stat-box"):
                                yield Label("[bold]Outgoing (Links To)[/bold]")
                                yield ListView(id="kg-outgoing-list")
                                with Horizontal():
                                    yield Select([], id="kg-link-target-select", prompt="Link to...")
                                    yield Button("Link", id="btn-kg-link", variant="primary", disabled=True)

                    # --- Tab 3: Context Chat ---
                    with TabPane("Chat", id="tab-kg-chat"):
                        yield Label("Chat with this node (and its neighbors) as context.")
                        yield RichLog(id="kg-chat-log", wrap=True, highlight=True, markup=True)
                        with Horizontal():
                            yield Input(placeholder="Ask a question...", id="kg-chat-input")
                            yield Select.from_values(["gemini", "cursor", "local"], id="kg-agent-select", value="gemini")

    def on_mount(self) -> None:
        self.load_nodes()

    def load_nodes(self, query: str = "") -> None:
        list_view = self.query_one("#kg-node-list", ListView)
        list_view.clear()

        if query:
            nodes = self.manager.search_knowledge(query)
        else:
            nodes = self.manager.list_knowledge()

        self.all_nodes_cache = nodes # Cache for linking select box

        if not nodes:
            list_view.append(ListItem(Label("[dim]No nodes found.[/dim]")))
            return

        for node in nodes:
            # Truncate content for display
            display = (node.content[:40] + "...") if len(node.content) > 40 else node.content
            item = ListItem(Label(f"[{node.category}] {display}"))
            item.node_id = node.id
            list_view.append(item)

    @on(Input.Changed, "#kg-search-input")
    def on_search_change(self, event: Input.Changed) -> None:
        self.load_nodes(query=event.value)

    @on(Button.Pressed, "#btn-kg-refresh")
    def on_refresh(self) -> None:
        self.load_nodes()
        if self.selected_node_id:
            self.load_node_details(self.selected_node_id)

    @on(Button.Pressed, "#btn-kg-new")
    def on_new_node(self) -> None:
        # Create a placeholder node and select it
        try:
            node = self.manager.add_knowledge("New Knowledge Node", category="GENERAL")
            self.notify("Node created.")
            self.load_nodes()
            self.load_node_details(node.id)
            # Switch to content tab
            self.query_one("#kg-tabs", TabbedContent).active = "tab-kg-content"
            self.query_one("#kg-content-editor", TextArea).focus()
        except Exception as e:
            self.notify(f"Error creating node: {e}", severity="error")

    @on(ListView.Selected, "#kg-node-list")
    def on_node_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "node_id"):
            self.load_node_details(event.item.node_id)

    def load_node_details(self, node_id: int) -> None:
        self.selected_node_id = node_id

        # 1. Load Content
        # We need to fetch the specific node.
        # Ideally manager should have get_node, but searching by ID via existing list is fine or query DB.
        # Let's find it in cache or re-fetch.
        node = next((n for n in self.all_nodes_cache if n.id == node_id), None)

        # If not in cache (e.g. search filter), re-fetch via list_knowledge (inefficient but safe)
        if not node:
            # Fallback: re-fetch all to find it or implement get_knowledge(id)
            # For now, let's assume it's in the list or we fetch links which gives content
            pass

        # Actually, get_links_for_item returns dicts, not the main node.
        # We should use the TextArea to edit content.
        # But wait, we need the content of the SELECTED node.
        # I'll update KnowledgeManager to have get_knowledge(id) in a future iteration or just query DB here?
        # No, I should stick to using manager. Let's use search_knowledge with unique content? No.

        # HACK: Use the all_nodes_cache correctly.
        if not node:
             # Just reload all to find it.
             all_nodes = self.manager.list_knowledge()
             node = next((n for n in all_nodes if n.id == node_id), None)

        if not node:
            self.notify("Node not found.", severity="error")
            return

        self.query_one("#kg-header-lbl", Label).update(f"[bold]Node {node.id}: {node.category}[/bold]")

        editor = self.query_one("#kg-content-editor", TextArea)
        editor.text = node.content
        editor.disabled = False

        self.query_one("#btn-kg-save").disabled = False
        self.query_one("#btn-kg-delete").disabled = False
        self.query_one("#btn-kg-link").disabled = False

        # 2. Load Links
        self.load_links(node_id)

        # 3. Update Link Target Select
        # Exclude self
        options = []
        for n in self.all_nodes_cache:
            if n.id != node_id:
                display = (n.content[:30] + "...") if len(n.content) > 30 else n.content
                options.append((f"{n.id}: {display}", str(n.id))) # Value must be string for Select

        select = self.query_one("#kg-link-target-select", Select)
        select.set_options(options)

    def load_links(self, node_id: int) -> None:
        links = self.manager.get_links_for_item(node_id)

        # Outgoing
        out_list = self.query_one("#kg-outgoing-list", ListView)
        out_list.clear()
        for l in links["outgoing"]:
            display = (l['content'][:40] + "...") if len(l['content']) > 40 else l['content']
            label = f"-> [{l['relation']}] {display} (ID: {l['target_id']})"
            item = ListItem(Label(label))
            item.link_id = l['link_id']
            item.target_node_id = l['target_id']
            out_list.append(item)

        # Incoming
        in_list = self.query_one("#kg-incoming-list", ListView)
        in_list.clear()
        for l in links["incoming"]:
            display = (l['content'][:40] + "...") if len(l['content']) > 40 else l['content']
            label = f"<- [{l['relation']}] {display} (ID: {l['source_id']})"
            item = ListItem(Label(label))
            item.link_id = l['link_id']
            item.source_node_id = l['source_id']
            in_list.append(item)

    @on(Button.Pressed, "#btn-kg-save")
    def on_save(self) -> None:
        if not self.selected_node_id: return

        content = self.query_one("#kg-content-editor", TextArea).text

        if self.manager.update_knowledge(self.selected_node_id, content):
            self.notify("Saved.")
            self.load_nodes() # Refresh list text
        else:
            self.notify("Error updating node.", severity="error")

    @on(Button.Pressed, "#btn-kg-delete")
    def on_delete(self) -> None:
        if not self.selected_node_id: return

        if self.manager.delete_knowledge(self.selected_node_id):
            self.notify("Node deleted.")
            self.selected_node_id = None
            self.query_one("#kg-content-editor", TextArea).text = ""
            self.query_one("#kg-content-editor", TextArea).disabled = True
            self.load_nodes()
        else:
            self.notify("Error deleting node.", severity="error")

    @on(Button.Pressed, "#btn-kg-link")
    def on_link(self) -> None:
        if not self.selected_node_id: return

        target_val = self.query_one("#kg-link-target-select", Select).value
        if not target_val:
            self.notify("Select a target node.", severity="warning")
            return

        target_id = int(target_val)

        if self.manager.link_items(self.selected_node_id, target_id):
            self.notify("Linked.")
            self.load_links(self.selected_node_id)
        else:
            self.notify("Failed to link.", severity="error")

    # Handle Link Traversal / Deletion
    # Textual ListView doesn't have specific "Delete" button per item easily.
    # We can use "Selected" to traverse.
    @on(ListView.Selected, "#kg-outgoing-list")
    def on_outgoing_select(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "target_node_id"):
            self.load_node_details(event.item.target_node_id)

    @on(ListView.Selected, "#kg-incoming-list")
    def on_incoming_select(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "source_node_id"):
            self.load_node_details(event.item.source_node_id)

    # --- Chat Logic ---
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "kg-chat-input":
            await self.handle_chat(event.value)
            event.input.value = ""

    async def handle_chat(self, message: str) -> None:
        if not message: return

        log = self.query_one("#kg-chat-log", RichLog)
        log.write(f"[bold blue]You:[/bold blue] {message}")

        agent_type = self.query_one("#kg-agent-select", Select).value or "gemini"

        # Build Context
        context_str = ""
        if self.selected_node_id:
            # Get node content and neighbors
            node_content = self.query_one("#kg-content-editor", TextArea).text
            links = self.manager.get_links_for_item(self.selected_node_id)

            context_str = f"Current Knowledge Node (ID {self.selected_node_id}):\n{node_content}\n\nRelated Nodes:\n"
            for l in links["outgoing"]:
                context_str += f"- Links To (ID {l['target_id']}): {l['content']}\n"
            for l in links["incoming"]:
                context_str += f"- Linked From (ID {l['source_id']}): {l['content']}\n"

        # Construct full query
        full_query = f"Context:\n{context_str}\n\nQuestion: {message}" if context_str else message

        log.write(f"[italic]Agent ({agent_type}) thinking...[/italic]")

        # Capture output
        output_capture = io.StringIO()
        success = False

        with contextlib.redirect_stdout(output_capture):
            try:
                success = await run_ask_logic(
                    query=full_query,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    verbose=False
                )
            except Exception as e:
                output_capture.write(f"Error: {e}")

        response = output_capture.getvalue()

        if success:
            log.write(f"[bold green]Agent:[/bold green] {response}")
        else:
            log.write(f"[bold red]Error:[/bold red] {response}")
