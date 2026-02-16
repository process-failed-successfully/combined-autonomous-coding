import asyncio
import sys
import signal
from typing import Optional, Callable

try:
    from rich.console import Console
    console = Console()
    print = console.print
except ImportError:
    pass

class SockLabManager:
    """
    Manages raw socket interactions (TCP).
    """

    def __init__(self):
        self.stop_event = asyncio.Event()
        self.writer = None

    async def _read_stdin(self, writer: asyncio.StreamWriter):
        """Reads from stdin and sends to the socket."""
        loop = asyncio.get_running_loop()
        print("[dim]Type your message and press Enter to send. Ctrl+C to quit.[/dim]")
        while not self.stop_event.is_set():
            try:
                # Use executor to avoid blocking the event loop
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line: # EOF
                    self.stop_event.set()
                    break

                # We send exactly what we read (including newline)
                # or should we strip? Netcat usually sends what you type.
                # sys.stdin.readline() keeps the \n.
                data = line.encode()
                writer.write(data)
                await writer.drain()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[red]Error reading stdin: {e}[/red]")
                self.stop_event.set()
                break

    async def _read_socket(self, reader: asyncio.StreamReader):
        """Reads from the socket and prints to stdout."""
        while not self.stop_event.is_set():
            try:
                data = await reader.read(4096)
                if not data: # EOF
                    print("[yellow]Connection closed by remote host.[/yellow]")
                    self.stop_event.set()
                    break

                # Print raw data decoded as utf-8, replacing errors
                text = data.decode('utf-8', errors='replace')
                # We use sys.stdout.write to avoid adding extra newlines if the data has them
                sys.stdout.write(text)
                sys.stdout.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[red]Error reading socket: {e}[/red]")
                self.stop_event.set()
                break

    async def start_client(self, host: str, port: int):
        """Starts a TCP client."""
        print(f"Connecting to {host}:{port}...")
        try:
            reader, writer = await asyncio.open_connection(host, port)
            self.writer = writer
            print(f"[green]Connected to {host}:{port}[/green]")
            await self._interactive_loop(reader, writer)
        except Exception as e:
            print(f"[red]Connection failed: {e}[/red]")
            sys.exit(1)

    async def start_server(self, host: str, port: int):
        """Starts a TCP server."""
        # For a simple netcat-like server, we usually handle one connection at a time interactively,
        # or we could broadcast. Let's handle the first connection interactively for simplicity.

        server_future = asyncio.get_running_loop().create_future()

        async def handle_client(reader, writer):
            addr = writer.get_extra_info('peername')
            print(f"[green]Accepted connection from {addr}[/green]")
            self.writer = writer

            # We only handle one session for interactive mode
            await self._interactive_loop(reader, writer)

            print(f"[yellow]Connection closed from {addr}[/yellow]")
            writer.close()
            await writer.wait_closed()
            server_future.set_result(True)

        server = await asyncio.start_server(handle_client, host, port)
        addr = server.sockets[0].getsockname()
        print(f"Listening on {addr}...")

        async with server:
            # serve_forever() would keep accepting.
            # But for interactive tool, we often want to exit after the session end?
            # Or keep listening? 'nc -l' usually exits after connection closes unless -k is passed.
            # Let's stick to "exit after one session" for now as it's simpler for a "Lab" tool.
            # We wait for the first handler to finish.
            await server_future

    async def _interactive_loop(self, reader, writer):
        """Runs the read/write loop."""
        tasks = [
            asyncio.create_task(self._read_stdin(writer)),
            asyncio.create_task(self._read_socket(reader))
        ]

        # Signal handling for Ctrl+C
        loop = asyncio.get_running_loop()
        def signal_handler():
            print("\n[yellow]Stopping...[/yellow]")
            self.stop_event.set()

        try:
            if sys.platform != "win32":
                loop.add_signal_handler(signal.SIGINT, signal_handler)
        except NotImplementedError:
            pass

        # Wait for stop event (connection closed or Ctrl+C)
        await self.stop_event.wait()

        # Cancel tasks
        for t in tasks:
            t.cancel()

        # Wait for tasks to finish cancelling
        await asyncio.gather(*tasks, return_exceptions=True)

        # Remove signal handler
        try:
            if sys.platform != "win32":
                loop.remove_signal_handler(signal.SIGINT)
        except Exception:
            pass

async def run_sock_lab_logic(args):
    """Entry point for sock-lab."""
    manager = SockLabManager()

    # Determine Host/Port
    # args structure depends on how we define it in main.py.
    # Let's assume:
    # sock-lab connect <host> <port>
    # sock-lab listen <port> [--host <host>]

    if args.action == "connect":
        await manager.start_client(args.host, args.port)
    elif args.action == "listen":
        host = args.host if args.host else "0.0.0.0"  # nosec
        await manager.start_server(host, args.port)
    else:
        print(f"Unknown action: {args.action}")
        sys.exit(1)
