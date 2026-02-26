import asyncio
import sys
import signal
from typing import Optional, Callable

# CLI compatibility helper
try:
    from rich.console import Console
    console = Console()
    print_cli = console.print
except ImportError:
    print_cli = print

class SockLabManager:
    """
    Manages raw socket interactions (TCP).
    Decoupled from CLI I/O to support TUI.
    """

    def __init__(self):
        self.stop_event = asyncio.Event()
        self.writer: Optional[asyncio.StreamWriter] = None
        self.reader: Optional[asyncio.StreamReader] = None

    async def send_data(self, data: bytes):
        """Sends data to the connected socket."""
        if self.writer:
            try:
                self.writer.write(data)
                await self.writer.drain()
            except Exception:
                # Connection might be closed
                pass

    async def _read_socket(self, reader: asyncio.StreamReader, on_data: Callable[[bytes], None], on_error: Callable[[str], None]):
        """Reads from the socket and calls the callback."""
        while not self.stop_event.is_set():
            try:
                data = await reader.read(4096)
                if not data: # EOF
                    on_error("Connection closed by remote host.")
                    self.stop_event.set()
                    break

                on_data(data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                on_error(f"Error reading socket: {e}")
                self.stop_event.set()
                break

    async def start_client(self, host: str, port: int, on_data: Callable[[bytes], None], on_error: Callable[[str], None], on_connect: Optional[Callable[[], None]] = None):
        """Starts a TCP client."""
        try:
            self.reader, self.writer = await asyncio.open_connection(host, port)
            if on_connect:
                on_connect()

            await self._read_socket(self.reader, on_data, on_error)
        except Exception as e:
            on_error(f"Connection failed: {e}")
        finally:
            self.stop()

    async def start_server(self, host: str, port: int, on_data: Callable[[bytes], None], on_error: Callable[[str], None], on_connect: Optional[Callable[[str], None]] = None):
        """Starts a TCP server (single connection for interactive mode)."""
        server_future = asyncio.get_running_loop().create_future()

        async def handle_client(reader, writer):
            addr = writer.get_extra_info('peername')
            if on_connect:
                on_connect(str(addr))

            self.reader = reader
            self.writer = writer

            await self._read_socket(reader, on_data, on_error)

            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            if not server_future.done():
                server_future.set_result(True)

        try:
            server = await asyncio.start_server(handle_client, host, port)
            # Note: The caller must handle printing "Listening on..." if desired, or we can use a callback.
            # But here we don't have a callback for "Listening started".
            # Ideally we could add one, but 'on_connect' handles the client connection.

            async with server:
                await server_future
        except Exception as e:
            on_error(f"Server error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stops the connection."""
        self.stop_event.set()
        if self.writer:
            try:
                self.writer.close()
            except Exception:
                pass

async def run_sock_lab_logic(args):
    """Entry point for sock-lab CLI."""
    manager = SockLabManager()

    # CLI Callbacks
    def on_data(data: bytes):
        # Print raw data decoded as utf-8, replacing errors
        text = data.decode('utf-8', errors='replace')
        sys.stdout.write(text)
        sys.stdout.flush()

    def on_error(msg: str):
        print_cli(f"[red]{msg}[/red]")

    def on_connect_client():
        print_cli(f"[green]Connected to {args.host}:{args.port}[/green]")
        print_cli("[dim]Type your message and press Enter to send. Ctrl+C to quit.[/dim]")

    def on_connect_server(addr: str):
        print_cli(f"[green]Accepted connection from {addr}[/green]")

    # Stdin reader for CLI
    async def read_stdin():
        loop = asyncio.get_running_loop()
        while not manager.stop_event.is_set():
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    manager.stop()
                    break
                await manager.send_data(line.encode())
            except asyncio.CancelledError:
                break
            except Exception as e:
                on_error(f"Error reading stdin: {e}")
                manager.stop()
                break

    # Setup CLI execution
    tasks = []

    if args.action == "connect":
        print_cli(f"Connecting to {args.host}:{args.port}...")
        client_task = asyncio.create_task(manager.start_client(args.host, args.port, on_data, on_error, on_connect_client))
        tasks.append(client_task)
    elif args.action == "listen":
        host = args.host if args.host else "0.0.0.0" # nosec
        print_cli(f"Listening on {host}:{args.port}...")
        server_task = asyncio.create_task(manager.start_server(host, args.port, on_data, on_error, on_connect_server))
        tasks.append(server_task)
    else:
        print(f"Unknown action: {args.action}")
        sys.exit(1)

    # Start stdin reader
    stdin_task = asyncio.create_task(read_stdin())
    tasks.append(stdin_task)

    # Signal handling
    loop = asyncio.get_running_loop()
    def signal_handler():
        print_cli("\n[yellow]Stopping...[/yellow]")
        manager.stop()

    try:
        if sys.platform != "win32":
            loop.add_signal_handler(signal.SIGINT, signal_handler)
    except NotImplementedError:
        pass

    # Wait for completion
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    except asyncio.CancelledError:
        pass

    # Cancel others
    for t in tasks:
        if not t.done():
            t.cancel()

    # Wait for cancellations
    await asyncio.gather(*tasks, return_exceptions=True)

    try:
        if sys.platform != "win32":
            loop.remove_signal_handler(signal.SIGINT)
    except Exception:
        pass
