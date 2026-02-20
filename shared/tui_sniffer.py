from pathlib import Path
from typing import Optional, List
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Label, Select, Checkbox, RichLog, Input
from textual import on
from rich.text import Text

from shared.sniffer_lab import SnifferManager, Packet


class SnifferLabTab(Container):
    """Tab for Network Packet Sniffing."""

    def __init__(self, project_dir: Optional[Path] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = SnifferManager()
        self.packets: List[Packet] = []  # Store packet objects
        self.is_capturing = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Packet Sniffer Lab[/bold]", classes="welcome-text")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Label("Interface:", classes="label")
                yield Select([], id="sniff-interface", prompt="Select Interface")
                yield Button("Start Capture", id="btn-sniff-start", variant="primary")
                yield Button("Stop", id="btn-sniff-stop", variant="error", disabled=True)
                yield Button("Clear", id="btn-sniff-clear", variant="default")
                yield Checkbox("Demo Mode", id="chk-sniff-demo", value=False)

            with Horizontal(classes="stat-box"):
                yield Label("Filter:", classes="label")
                yield Input(placeholder="Filter by IP, Port, or Protocol...", id="sniff-filter")

            # Packet List
            with Vertical(id="sniff-list-container"):
                yield DataTable(id="sniff-table")

            # Packet Details
            with VerticalScroll(id="sniff-details-container", classes="stat-box"):
                yield Label("[bold]Packet Details[/bold]")
                yield RichLog(id="sniff-details-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        # Setup Table
        table = self.query_one("#sniff-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("No.", "Time", "Source", "Destination", "Protocol", "Length", "Info")

        # Load Interfaces
        self.load_interfaces()

    def load_interfaces(self) -> None:
        try:
            ifaces = self.manager.get_interfaces()
            select = self.query_one("#sniff-interface", Select)
            options = [(i, i) for i in ifaces]
            if not options:
                options = [("No interfaces found", "")]
            select.set_options(options)
            if options:
                select.value = options[0][1]
        except Exception as e:
            self.notify(f"Error loading interfaces: {e}", severity="error")

    @on(Button.Pressed, "#btn-sniff-start")
    def on_start(self) -> None:
        interface_val = self.query_one("#sniff-interface", Select).value
        # Handle Select.BLANK or None
        if interface_val == Select.BLANK or interface_val is None:
            interface = ""
        else:
            interface = str(interface_val)

        demo_mode = self.query_one("#chk-sniff-demo", Checkbox).value

        if not interface and not demo_mode:
            self.notify("Please select an interface.", severity="error")
            return

        self.is_capturing = True
        self.query_one("#btn-sniff-start").disabled = True
        self.query_one("#btn-sniff-stop").disabled = False
        self.query_one("#chk-sniff-demo", Checkbox).disabled = True
        self.query_one("#sniff-interface").disabled = True

        try:
            if demo_mode:
                self.manager.start_demo_capture(self.handle_packet)
                self.notify("Started Demo Capture.")
            else:
                self.manager.start_capture(interface, self.handle_packet)
                self.notify(f"Started capture on {interface}.")
        except PermissionError:
            self.notify("Permission Denied: Root required for raw sockets.", severity="error")
            self.notify("Switching to Demo Mode automatically.", severity="warning")
            self.query_one("#chk-sniff-demo", Checkbox).value = True
            # Retry with demo
            try:
                self.manager.start_demo_capture(self.handle_packet)
            except Exception as e:
                self.notify(f"Demo failed: {e}", severity="error")
                self.on_stop()
        except Exception as e:
            self.notify(f"Capture failed: {e}", severity="error")
            self.on_stop()

    @on(Button.Pressed, "#btn-sniff-stop")
    def on_stop(self) -> None:
        self.manager.stop_capture()
        self.is_capturing = False

        self.query_one("#btn-sniff-start").disabled = False
        self.query_one("#btn-sniff-stop").disabled = True
        self.query_one("#chk-sniff-demo", Checkbox).disabled = False
        self.query_one("#sniff-interface").disabled = False

        self.notify("Capture stopped.")

    @on(Button.Pressed, "#btn-sniff-clear")
    def on_clear(self) -> None:
        self.packets = []
        self.query_one("#sniff-table", DataTable).clear()
        self.query_one("#sniff-details-log", RichLog).clear()

    def handle_packet(self, packet: Packet) -> None:
        """Callback from background thread."""
        if not self.is_capturing:
            return

        # Schedule update on main thread
        self.app.call_from_thread(self.add_packet_to_ui, packet)

    def add_packet_to_ui(self, packet: Packet) -> None:
        # Apply filter
        filter_text = self.query_one("#sniff-filter", Input).value.lower()
        if filter_text:
            search_str = f"{packet.src_ip} {packet.dst_ip} {packet.info} {packet.proto_l3}".lower()
            if filter_text not in search_str:
                return

        self.packets.append(packet)
        idx = len(self.packets) - 1  # 0-based index

        table = self.query_one("#sniff-table", DataTable)

        # Format columns
        ts = datetime.fromtimestamp(packet.timestamp).strftime('%H:%M:%S.%f')[:-3]

        # Protocol Name
        proto = "IP"
        if packet.proto_l3 == 6:
            proto = "TCP"
        elif packet.proto_l3 == 17:
            proto = "UDP"
        elif packet.proto_l3 == 1:
            proto = "ICMP"
        elif packet.proto_l2 != 8 and packet.proto_l2 != 2048:
            proto = "ARP/Other"

        table.add_row(
            str(idx + 1),
            ts,
            packet.src_ip or packet.src_mac,
            packet.dst_ip or packet.dst_mac,
            proto,
            str(packet.payload_len),
            packet.info,
            key=str(idx)  # Use index as key
        )

        # Auto-scroll (only if near bottom? Textual does this automatically usually)
        # table.scroll_end(animate=False)

    @on(DataTable.RowSelected, "#sniff-table")
    def on_packet_selected(self, event: DataTable.RowSelected) -> None:
        try:
            # Check if row_key is valid
            if not event.row_key.value:
                return

            idx = int(event.row_key.value)
            if 0 <= idx < len(self.packets):
                packet = self.packets[idx]
                self.show_details(packet)
        except (ValueError, IndexError):
            pass

    def show_details(self, packet: Packet) -> None:
        log = self.query_one("#sniff-details-log", RichLog)
        log.clear()

        log.write(f"[bold]Packet #{self.packets.index(packet) + 1}[/bold]")
        log.write(f"Timestamp: {packet.timestamp}")
        log.write(f"Ethernet: {packet.src_mac} -> {packet.dst_mac} (Type: {packet.proto_l2})")

        if packet.src_ip:
            log.write(f"IP: {packet.src_ip} -> {packet.dst_ip} (Proto: {packet.proto_l3})")

        if packet.src_port:
            log.write(f"Transport: Port {packet.src_port} -> {packet.dst_port}")

        log.write(f"Info: {packet.info}")
        log.write("\n[bold]Hex Dump:[/bold]")

        hexdump_str = self.hexdump(packet.raw_data)
        log.write(Text(hexdump_str, style="dim"))

    def hexdump(self, src: bytes, length: int = 16) -> str:
        FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
        lines = []
        for c in range(0, len(src), length):
            chars = src[c:c + length]
            hex_part = ' '.join(f"{x:02x}" for x in chars)
            printable = ''.join(FILTER[x] for x in chars)
            lines.append(f"{c:04x}  {hex_part:<{length * 3}}  {printable}")
        return '\n'.join(lines)
