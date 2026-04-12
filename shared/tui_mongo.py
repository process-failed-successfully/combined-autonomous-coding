from pathlib import Path
import asyncio
from typing import Optional, List
from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, ListView, ListItem, TextArea, RichLog, Select
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.mongo_lab import MongoLabManager

try:
    from bson import json_util
except ImportError:
    json_util = None

class MongoLabTab(Container):
    """
    MongoDB Management Tab.
    Supports viewing databases, collections, and finding/inserting documents.
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = MongoLabManager()
        self.current_db: Optional[str] = None
        self.current_col: Optional[str] = None
        self.current_docs: List[dict] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Connection & Nav
            with Vertical(id="mongo-sidebar", classes="stat-box", styles="width: 30%;"):
                yield Label("[bold]MongoDB[/bold]")

                # Connection
                yield Label("URL:")
                yield Input(value="mongodb://localhost:27017/", id="mongo-url-input")
                yield Button("Connect", id="btn-mongo-connect", variant="primary")
                yield Label("Not Connected", id="lbl-mongo-status", classes="status-text")

                yield Label("[bold]Databases[/bold]")
                yield Select([], id="mongo-db-select", prompt="Select Database")

                yield Label("[bold]Collections[/bold]")
                yield Select([], id="mongo-col-select", prompt="Select Collection")
                yield Button("Refresh Nav", id="btn-mongo-refresh-nav", variant="default")


            # Right Pane: Inspector & Editor
            with Vertical(id="mongo-main", styles="width: 70%;"):
                # Header Info
                with Horizontal(classes="stat-box"):
                    with Vertical():
                        yield Label("DB:", classes="label")
                        yield Label("None", id="lbl-mongo-db", classes="value")
                    with Vertical():
                        yield Label("Collection:", classes="label")
                        yield Label("-", id="lbl-mongo-col", classes="value")

                with Horizontal():
                    with Vertical(styles="width: 50%;"):
                        yield Label("[bold]Query (JSON)[/bold]")
                        yield TextArea("{}", id="mongo-query-editor", language="json", styles="height: 10;")
                    with Vertical(styles="width: 50%; padding-left: 1;"):
                        yield Label("[bold]Limit[/bold]")
                        yield Input("100", id="mongo-limit-input")

                with Horizontal(classes="stat-box"):
                     yield Button("Find", id="btn-mongo-find", variant="primary", disabled=True)
                     yield Button("Insert Document", id="btn-mongo-insert", variant="warning", disabled=True)

                yield Label("[bold]Documents[/bold]")
                yield TextArea(id="mongo-docs-editor", language="json")

                # Log
                yield Label("[bold]Log[/bold]")
                yield RichLog(id="mongo-log", wrap=True, highlight=True, markup=True, styles="height: 10;")

    def on_mount(self) -> None:
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-mongo-connect":
            await self.connect_mongo()
        elif event.button.id == "btn-mongo-refresh-nav":
            await self.refresh_nav()
        elif event.button.id == "btn-mongo-find":
            await self.find_docs()
        elif event.button.id == "btn-mongo-insert":
            await self.insert_doc()

    @on(Select.Changed, "#mongo-db-select")
    async def on_db_changed(self, event: Select.Changed) -> None:
        if event.value and event.value != Select.BLANK:
             self.current_db = str(event.value)
             self.query_one("#lbl-mongo-db", Label).update(self.current_db)
             await self.load_cols(self.current_db)

    @on(Select.Changed, "#mongo-col-select")
    async def on_col_changed(self, event: Select.Changed) -> None:
         if event.value and event.value != Select.BLANK:
              self.current_col = str(event.value)
              self.query_one("#lbl-mongo-col", Label).update(self.current_col)
              self.query_one("#btn-mongo-find").disabled = False
              self.query_one("#btn-mongo-insert").disabled = False

    async def connect_mongo(self) -> None:
        url = self.query_one("#mongo-url-input", Input).value
        self.manager = MongoLabManager(url)

        lbl = self.query_one("#lbl-mongo-status", Label)
        lbl.update("Connecting...")

        success = await asyncio.to_thread(self.manager.connect)

        if success:
            lbl.update("[green]Connected[/green]")
            self.notify("Connected to MongoDB.")
            await self.load_dbs()
        else:
            lbl.update("[red]Failed[/red]")
            self.notify("Failed to connect.", severity="error")

    async def refresh_nav(self) -> None:
         await self.load_dbs()

    async def load_dbs(self) -> None:
         self.log_message("Loading databases...")
         dbs = await asyncio.to_thread(self.manager.list_dbs)
         select = self.query_one("#mongo-db-select", Select)

         # Retain current selection if still valid
         current = select.value

         options = [(db, db) for db in sorted(dbs)]
         select.set_options(options)

         if current in dbs:
              select.value = current
         elif dbs:
              select.value = Select.BLANK

    async def load_cols(self, db_name: str) -> None:
         self.log_message(f"Loading collections for db '{db_name}'...")
         cols = await asyncio.to_thread(self.manager.list_cols, db_name)
         select = self.query_one("#mongo-col-select", Select)

         # Retain current selection if still valid
         current = select.value

         options = [(col, col) for col in sorted(cols)]
         select.set_options(options)

         if current in cols:
              select.value = current
         elif cols:
              select.value = Select.BLANK

    async def find_docs(self) -> None:
        if not self.current_db or not self.current_col:
             return

        query_text = self.query_one("#mongo-query-editor", TextArea).text.strip()
        limit_text = self.query_one("#mongo-limit-input", Input).value.strip()

        import json
        query = {}
        if query_text:
             try:
                  query = json_util.loads(query_text) if json_util else json.loads(query_text)
             except Exception as e:
                  self.notify("Invalid Query JSON", severity="error")
                  self.log_message(f"Error parsing query JSON: {e}")
                  return

        limit = 100
        if limit_text.isdigit():
             limit = int(limit_text)

        self.log_message(f"Finding documents in '{self.current_db}.{self.current_col}'...")
        docs = await asyncio.to_thread(self.manager.find, self.current_db, self.current_col, query, limit)
        self.current_docs = docs

        self.log_message(f"Found {len(docs)} documents.")

        editor = self.query_one("#mongo-docs-editor", TextArea)
        try:
             editor.text = json_util.dumps(docs, indent=2) if json_util else json.dumps(docs, indent=2, default=str)
        except Exception as e:
             editor.text = str(docs)
             self.log_message(f"Could not cleanly format docs: {e}")

    async def insert_doc(self) -> None:
        if not self.current_db or not self.current_col:
             return

        # Use whatever is in the query editor as the document to insert for simplicity
        doc_text = self.query_one("#mongo-query-editor", TextArea).text.strip()

        if not doc_text:
             self.notify("Provide document in Query editor", severity="error")
             return

        import json
        try:
             doc = json_util.loads(doc_text) if json_util else json.loads(doc_text)
        except Exception as e:
             self.notify("Invalid JSON Document", severity="error")
             self.log_message(f"Error parsing document JSON: {e}")
             return

        self.log_message(f"Inserting document into '{self.current_db}.{self.current_col}'...")
        inserted_id = await asyncio.to_thread(self.manager.insert, self.current_db, self.current_col, doc)

        if inserted_id:
             self.notify("Document inserted")
             self.log_message(f"Inserted document with ID: {inserted_id}")
             # Refresh find
             await self.find_docs()
        else:
             self.notify("Failed to insert", severity="error")


    def log_message(self, msg: str) -> None:
        self.query_one("#mongo-log", RichLog).write(msg)