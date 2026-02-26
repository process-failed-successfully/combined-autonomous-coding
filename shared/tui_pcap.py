from pathlib import Path
from typing import Optional, Iterable
import asyncio
import json

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    DirectoryTree,
    RichLog,
    Label,
    Button,
    Input,
    DataTable,
    TabbedContent,
    TabPane,
)
from textual import on
from shared.pcap_lab import PcapLabManager


class PcapDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [
            p for p in paths if p.is_dir() or p.suffix.lower() in {".pcap", ".cap", ".pcapng"}
        ]


class PcapLabTab(Container):
    """Tab for PCAP Analysis."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = PcapLabManager()
        self.selected_file: Optional[Path] = None
        self.packet_cache = {}

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: File Browser
            with Vertical(id="pcap-list-container", classes="stat-box"):
                yield Label("[bold]PCAP Files[/bold]")
                yield PcapDirectoryTree(str(self.project_dir), id="pcap-tree")
                yield Button("Load Selected", id="btn-pcap-load", variant="primary", disabled=True)

            # Right Pane: Content
            with Vertical(id="pcap-content-container"):
                with TabbedContent():
                    with TabPane("Summary"):
                        yield Label("[bold]File Statistics[/bold]")
                        yield RichLog(id="pcap-summary-log", wrap=True, highlight=True, markup=True)

                    with TabPane("Packets"):
                        with Horizontal(classes="stat-box"):
                            yield Label("Filter:")
                            yield Input(placeholder="proto=TCP, src=192.168.1.1...", id="pcap-filter-input")
                            yield Button("Apply", id="btn-pcap-filter", variant="default")

                        yield DataTable(id="pcap-table")

                    with TabPane("Packet Details"):
                        yield RichLog(id="pcap-detail-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#pcap-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("No.", "Time", "Source", "Destination", "Proto", "Len", "Info")

    @on(DirectoryTree.FileSelected, "#pcap-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.is_file():
            self.selected_file = path
            self.query_one("#btn-pcap-load").disabled = False
            self.notify(f"Selected: {path.name}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pcap-load":
            await self.load_pcap()
        elif event.button.id == "btn-pcap-filter":
            await self.filter_pcap()

    async def load_pcap(self) -> None:
        if not self.selected_file:
            return

        self.notify(f"Loading {self.selected_file.name}...")
        self.query_one("#pcap-summary-log", RichLog).clear()
        self.query_one("#pcap-detail-log", RichLog).clear()

        # Load Summary
        await self.load_summary()

        # Load Packets
        await self.filter_pcap()

    async def load_summary(self) -> None:
        log = self.query_one("#pcap-summary-log", RichLog)
        log.write("Analyzing...")

        try:
            stats = await asyncio.to_thread(self.manager.analyze, self.selected_file)

            if "error" in stats:
                log.clear()
                log.write(f"[bold red]Error:[/bold red] {stats['error']}")
                return

            log.clear()
            log.write(f"[bold]File:[/bold] {self.selected_file.name}")
            log.write(f"[bold]Total Packets:[/bold] {stats['packet_count']}")
            log.write(f"[bold]Duration:[/bold] {stats['duration']:.2f}s")

            if stats.get('start_time'):
                import time
                st = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['start_time']))
                et = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['end_time']))
                log.write(f"[bold]Start:[/bold] {st}")
                log.write(f"[bold]End:[/bold] {et}")

            log.write("\n[bold]Protocols:[/bold]")
            for p, c in stats['protocols'].items():
                log.write(f"  - {p}: {c}")

            log.write("\n[bold]Top Talkers:[/bold]")
            for ip, c in stats['top_talkers']:
                log.write(f"  - {ip}: {c}")

        except Exception as e:
            log.write(f"[red]Analysis failed: {e}[/red]")

    async def filter_pcap(self) -> None:
        if not self.selected_file:
            return

        table = self.query_one("#pcap-table", DataTable)
        table.clear()
        self.packet_cache = {}

        filter_str = self.query_one("#pcap-filter-input", Input).value
        # Simple parsing of filter string: proto=TCP, src=..., dst=...
        proto, src, dst = None, None, None

        if filter_str:
            parts = [p.strip() for p in filter_str.split(",")]
            for part in parts:
                if "=" in part:
                    k, v = part.split("=", 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if k == "proto": proto = v
                    elif k == "src": src = v
                    elif k == "dst": dst = v

        try:
            # We use list to consume generator for display (limited)
            # But wait, manager.filter_packets returns summaries.
            # We don't have a way to get FULL details for a specific packet easily
            # without re-reading or keeping file handle.
            # For this TUI, we'll just show summaries in table and maybe limited detail if possible.
            # The manager doesn't seem to support random access by index easily.
            # We will cache the summaries.

            def get_packets():
                return list(self.manager.filter_packets(
                    self.selected_file,
                    proto=proto,
                    src=src,
                    dst=dst,
                    limit=1000 # Reasonable limit for TUI
                ))

            packets = await asyncio.to_thread(get_packets)

            for pkt in packets:
                no = str(pkt["no"])
                table.add_row(
                    no,
                    pkt["time"],
                    pkt["src"] or "?",
                    pkt["dst"] or "?",
                    pkt["proto"],
                    str(pkt["len"]),
                    pkt["summary"] or "",
                    key=no
                )
                self.packet_cache[no] = pkt

            self.query_one("#pcap-table", DataTable).focus()
            self.notify(f"Loaded {len(packets)} packets.")

        except Exception as e:
            self.notify(f"Error loading packets: {e}", severity="error")

    @on(DataTable.RowSelected, "#pcap-table")
    def on_packet_selected(self, event: DataTable.RowSelected) -> None:
        key = event.row_key.value
        pkt = self.packet_cache.get(key)

        log = self.query_one("#pcap-detail-log", RichLog)
        log.clear()

        if pkt:
            log.write(f"[bold]Packet #{pkt['no']}[/bold]")
            log.write(json.dumps(pkt, indent=2))
            # Note: real deep inspection would require PcapReader to seek to offset.
            # The current PcapManager implementation is stream-based.
            # For now, we show what we have in summary.
