import json
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, TextArea, Label, ListView, ListItem, RichLog
from textual import on
from shared.mongo_lab import MongoLabManager


class MongoLabTab(Container):
    """Tab for MongoDB Lab to interactively query databases."""

    DEFAULT_CSS = """
    MongoLabTab {
        layout: vertical;
        height: 100%;
    }

    .row {
        height: auto;
        margin: 1;
        align: left middle;
    }

    #mongo-uri-input {
        width: 40;
    }

    .query-box {
        height: 1fr;
        margin: 1;
        border: solid $accent;
    }

    .query-actions {
        height: auto;
        margin-left: 1;
        margin-bottom: 1;
    }

    .status-msg {
        color: $warning;
        margin-left: 2;
    }

    #mongo-log {
        height: 1fr;
        margin: 1;
        border: solid $secondary;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = MongoLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]MongoDB Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="row"):
                yield Label("MongoDB URI:", classes="lbl")
                yield Input(id="mongo-uri-input", placeholder="mongodb://localhost:27017/", value="mongodb://localhost:27017/")
                yield Button("Connect", id="btn-mongo-connect", variant="primary")
                yield Label("Not Connected", id="mongo-status", classes="status-msg")

            with Horizontal(classes="row"):
                yield Input(id="mongo-db-input", placeholder="Database Name")
                yield Button("List DBs", id="btn-mongo-list-dbs", variant="default")
                yield Input(id="mongo-col-input", placeholder="Collection Name")
                yield Button("List Collections", id="btn-mongo-list-cols", variant="default")

            with Vertical(classes="query-box"):
                yield Label("JSON Query / Document:")
                yield TextArea(id="mongo-query", language="json", text="{}")

            with Horizontal(classes="query-actions"):
                yield Button("Find", id="btn-mongo-find", variant="success")
                yield Button("Insert", id="btn-mongo-insert", variant="primary")
                yield Button("Delete", id="btn-mongo-delete", variant="error")
                yield Button("Clear Output", id="btn-mongo-clear", variant="default")

            yield RichLog(id="mongo-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if not btn_id:
            return

        status_lbl = self.query_one("#mongo-status", Label)
        log_view = self.query_one("#mongo-log", RichLog)

        if btn_id == "btn-mongo-connect":
            uri = self.query_one("#mongo-uri-input", Input).value.strip() or "mongodb://localhost:27017/"
            try:
                self.manager = MongoLabManager(uri)
                if self.manager.connect():
                    status_lbl.update(f"Connected")
                    self.notify(f"Connected to MongoDB")
                else:
                    status_lbl.update("Connection Failed")
                    self.notify("Failed to connect to MongoDB", severity="error")
            except Exception as e:
                status_lbl.update(f"Error")
                self.notify(f"Connection error: {e}", severity="error")

        elif btn_id == "btn-mongo-list-dbs":
            dbs = self.manager.list_dbs()
            log_view.write("Databases:")
            if dbs:
                for db in dbs:
                    log_view.write(f" - {db}")
            else:
                log_view.write("(empty)")

        elif btn_id == "btn-mongo-list-cols":
            db_name = self.query_one("#mongo-db-input", Input).value.strip()
            if not db_name:
                self.notify("Database name required.", severity="warning")
                return
            cols = self.manager.list_cols(db_name)
            log_view.write(f"Collections in '{db_name}':")
            if cols:
                for col in cols:
                    log_view.write(f" - {col}")
            else:
                log_view.write("(empty)")

        elif btn_id == "btn-mongo-find":
            db_name = self.query_one("#mongo-db-input", Input).value.strip()
            col_name = self.query_one("#mongo-col-input", Input).value.strip()
            if not db_name or not col_name:
                self.notify("Database and Collection names required.", severity="warning")
                return

            query_str = self.query_one("#mongo-query", TextArea).text.strip()
            try:
                query = json.loads(query_str) if query_str else {}
            except json.JSONDecodeError as e:
                self.notify(f"Invalid JSON: {e}", severity="error")
                return

            docs = self.manager.find(db_name, col_name, query)
            log_view.write(f"Find Results ({len(docs)}):")
            log_view.write(json.dumps(docs, indent=2))

        elif btn_id == "btn-mongo-insert":
            db_name = self.query_one("#mongo-db-input", Input).value.strip()
            col_name = self.query_one("#mongo-col-input", Input).value.strip()
            if not db_name or not col_name:
                self.notify("Database and Collection names required.", severity="warning")
                return

            doc_str = self.query_one("#mongo-query", TextArea).text.strip()
            try:
                doc = json.loads(doc_str)
            except json.JSONDecodeError as e:
                self.notify(f"Invalid JSON: {e}", severity="error")
                return

            inserted_id = self.manager.insert(db_name, col_name, doc)
            if inserted_id:
                log_view.write(f"Inserted document with ID: {inserted_id}")
                self.notify("Document inserted.")
            else:
                self.notify("Insert failed.", severity="error")

        elif btn_id == "btn-mongo-delete":
            db_name = self.query_one("#mongo-db-input", Input).value.strip()
            col_name = self.query_one("#mongo-col-input", Input).value.strip()
            if not db_name or not col_name:
                self.notify("Database and Collection names required.", severity="warning")
                return

            query_str = self.query_one("#mongo-query", TextArea).text.strip()
            try:
                query = json.loads(query_str) if query_str else {}
            except json.JSONDecodeError as e:
                self.notify(f"Invalid JSON: {e}", severity="error")
                return

            if not query:
                self.notify("Safety check: Cannot delete with empty query.", severity="warning")
                return

            deleted_count = self.manager.delete(db_name, col_name, query)
            log_view.write(f"Deleted {deleted_count} document(s).")
            self.notify(f"Deleted {deleted_count} document(s).")

        elif btn_id == "btn-mongo-clear":
            log_view.clear()
