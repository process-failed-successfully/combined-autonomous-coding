from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, DataTable, Button, ListView, ListItem, Input, RichLog
from textual import on
from shared.s3_lab import S3LabManager, HAS_BOTO3

class S3LabTab(Container):
    """Tab for interacting with S3 Buckets."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = None
        self.current_bucket = None
        self.current_prefix = ""
        self.delete_confirming = False

    def compose(self) -> ComposeResult:
        if not HAS_BOTO3:
            with Vertical(classes="stat-box"):
                yield Label("[bold red]boto3 not found[/bold red]")
                yield Label("Please install it to use S3 Lab:")
                yield Label("  pip install boto3")
            return

        with Horizontal():
            # Left Pane: Buckets
            with Vertical(id="s3-left-pane", classes="stat-box"):
                yield Label("[bold]Buckets[/bold]")
                yield ListView(id="s3-bucket-list")
                yield Button("Refresh", id="btn-s3-refresh", variant="default")

            # Center Pane: Object Browser
            with Vertical(id="s3-main-pane"):
                yield Label("[bold]Objects[/bold]", id="s3-objects-header")
                yield DataTable(id="s3-object-table")

                # Navigation / Breadcrumbs could go here
                with Horizontal(classes="stat-box"):
                    yield Button("Back", id="btn-s3-up", disabled=True)
                    yield Label("/", id="s3-path-lbl")

            # Right Pane: Actions
            with Vertical(id="s3-right-pane", classes="stat-box"):
                yield Label("[bold]Actions[/bold]")

                with Vertical(classes="stat-box"):
                    yield Label("Selected Object:")
                    yield Label("None", id="s3-selected-lbl")

                    yield Button("Download", id="btn-s3-download", variant="primary", disabled=True)
                    yield Button("Presign URL", id="btn-s3-presign", variant="warning", disabled=True)
                    yield Button("Delete", id="btn-s3-delete", variant="error", disabled=True)

                with Vertical(classes="stat-box"):
                    yield Label("Upload to current folder:")
                    yield Input(placeholder="Local file path...", id="s3-upload-input")
                    yield Button("Upload", id="btn-s3-upload", variant="success", disabled=True)

                yield Label("[bold]Log[/bold]")
                yield RichLog(id="s3-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        if HAS_BOTO3:
            try:
                self.manager = S3LabManager()
                self.load_buckets()

                # Setup table
                table = self.query_one("#s3-object-table", DataTable)
                table.cursor_type = "row"
                table.add_columns("Name", "Size", "Modified")
            except Exception as e:
                self.notify(f"Failed to init S3: {e}", severity="error")

    def load_buckets(self) -> None:
        list_view = self.query_one("#s3-bucket-list", ListView)
        list_view.clear()

        try:
            response = self.manager.s3_client.list_buckets()
            buckets = response.get("Buckets", [])

            for b in buckets:
                list_view.append(ListItem(Label(b["Name"]), name=b["Name"]))

        except Exception as e:
            self.query_one("#s3-log", RichLog).write(f"[red]Error listing buckets: {e}[/red]")

    @on(Button.Pressed, "#btn-s3-refresh")
    def on_refresh(self) -> None:
        self.load_buckets()
        self.notify("Buckets refreshed.")

    @on(ListView.Selected, "#s3-bucket-list")
    def on_bucket_selected(self, event: ListView.Selected) -> None:
        if not event.item:
            return

        label = event.item.query_one(Label)
        bucket_name = str(label.renderable)

        self.current_bucket = bucket_name
        self.current_prefix = ""
        self.load_objects()

        self.query_one("#s3-objects-header", Label).update(f"Objects in s3://{bucket_name}/")
        self.query_one("#s3-path-lbl", Label).update("/")
        self.query_one("#btn-s3-up").disabled = True
        self.query_one("#btn-s3-upload").disabled = False

        # Reset selection
        self.query_one("#s3-selected-lbl", Label).update("None")
        self.query_one("#btn-s3-download").disabled = True
        self.query_one("#btn-s3-presign").disabled = True
        self.query_one("#btn-s3-delete").disabled = True
        self._reset_delete_button()

    def load_objects(self) -> None:
        table = self.query_one("#s3-object-table", DataTable)
        table.clear()

        if not self.current_bucket:
            return

        try:
            paginator = self.manager.s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.current_bucket,
                Prefix=self.current_prefix,
                Delimiter='/'
            )

            for page in page_iterator:
                if "CommonPrefixes" in page:
                    for p in page["CommonPrefixes"]:
                        prefix = p["Prefix"]
                        folder_name = prefix[len(self.current_prefix):]
                        table.add_row(f"📁 {folder_name}", "-", "-", key=prefix)

                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        if key == self.current_prefix:
                            continue

                        name = key[len(self.current_prefix):]
                        size = str(obj["Size"])
                        mod = str(obj["LastModified"])
                        table.add_row(f"📄 {name}", size, mod, key=key)

        except Exception as e:
            self.query_one("#s3-log", RichLog).write(f"[red]Error listing objects: {e}[/red]")

    @on(DataTable.RowSelected, "#s3-object-table")
    def on_object_selected(self, event: DataTable.RowSelected) -> None:
        key = event.row_key.value
        self._reset_delete_button()

        if key.endswith("/"):
            self.current_prefix = key
            self.load_objects()
            self.query_one("#s3-path-lbl", Label).update(f"/{self.current_prefix}")
            self.query_one("#btn-s3-up").disabled = False
        else:
            self.query_one("#s3-selected-lbl", Label).update(key)
            self.query_one("#btn-s3-download").disabled = False
            self.query_one("#btn-s3-presign").disabled = False
            self.query_one("#btn-s3-delete").disabled = False

    @on(Button.Pressed, "#btn-s3-up")
    def on_up(self) -> None:
        self._reset_delete_button()
        if not self.current_prefix:
            return

        p = self.current_prefix.rstrip("/")
        if "/" in p:
            self.current_prefix = p.rsplit("/", 1)[0] + "/"
        else:
            self.current_prefix = ""

        self.load_objects()
        self.query_one("#s3-path-lbl", Label).update(f"/{self.current_prefix}")
        if not self.current_prefix:
            self.query_one("#btn-s3-up").disabled = True

    @on(Button.Pressed, "#btn-s3-presign")
    def on_presign(self) -> None:
        key = str(self.query_one("#s3-selected-lbl", Label).renderable)
        if not key or key == "None":
            return

        try:
            url = self.manager.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.current_bucket, 'Key': key},
                ExpiresIn=3600
            )
            log = self.query_one("#s3-log", RichLog)
            log.write(f"[bold green]Presigned URL (1h):[/bold green]")
            log.write(url)
            self.notify("URL generated.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    @on(Button.Pressed, "#btn-s3-download")
    def on_download(self) -> None:
        key = str(self.query_one("#s3-selected-lbl", Label).renderable)
        if not key or key == "None":
            return

        filename = Path(key).name
        local_path = filename

        self.notify(f"Downloading {filename}...")
        try:
            self.manager.s3_client.download_file(self.current_bucket, key, local_path)
            self.notify(f"Downloaded to {local_path}")
            self.query_one("#s3-log", RichLog).write(f"[green]Downloaded {key} to {local_path}[/green]")
        except Exception as e:
            self.notify(f"Download failed: {e}", severity="error")

    @on(Button.Pressed, "#btn-s3-upload")
    def on_upload(self) -> None:
        path_str = self.query_one("#s3-upload-input", Input).value
        if not path_str:
            self.notify("File path required.", severity="error")
            return

        path = Path(path_str)
        if not path.exists():
            self.notify("File not found.", severity="error")
            return

        key = self.current_prefix + path.name

        self.notify(f"Uploading {path.name}...")
        try:
            self.manager.s3_client.upload_file(str(path), self.current_bucket, key)
            self.notify("Upload successful.")
            self.query_one("#s3-upload-input", Input).value = ""
            self.load_objects()
        except Exception as e:
            self.notify(f"Upload failed: {e}", severity="error")

    @on(Button.Pressed, "#btn-s3-delete")
    def on_delete(self) -> None:
        key = str(self.query_one("#s3-selected-lbl", Label).renderable)
        if not key or key == "None":
            return

        btn = self.query_one("#btn-s3-delete", Button)

        if not self.delete_confirming:
            self.delete_confirming = True
            btn.label = "Confirm Delete?"
            return

        # Confirmed
        try:
            self.manager.s3_client.delete_object(Bucket=self.current_bucket, Key=key)
            self.notify(f"Deleted {key}")
            self.load_objects()
            self.query_one("#s3-selected-lbl", Label).update("None")
            self.query_one("#btn-s3-download").disabled = True
            self.query_one("#btn-s3-presign").disabled = True
            btn.disabled = True
        except Exception as e:
            self.notify(f"Delete failed: {e}", severity="error")
        finally:
            self._reset_delete_button()

    def _reset_delete_button(self):
        self.delete_confirming = False
        btn = self.query_one("#btn-s3-delete", Button)
        btn.label = "Delete"
