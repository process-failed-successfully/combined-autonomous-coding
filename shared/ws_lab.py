import asyncio
import sys
import signal
import websockets
from typing import Optional, List, Set

try:
    from rich.console import Console
    console = Console()
    print = console.print
except ImportError:
    pass

class WsLabManager:
    """
    Manages WebSocket interactions (Client and Server).
    """

    def __init__(self):
        self.stop_event = asyncio.Event()
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()

    async def _read_stdin(self, websocket):
        loop = asyncio.get_running_loop()
        while not self.stop_event.is_set():
            try:
                # Run blocking input in executor to avoid blocking the event loop
                message = await loop.run_in_executor(None, sys.stdin.readline)
                if not message: # EOF
                    self.stop_event.set()
                    break
                message = message.strip()
                if message:
                    await websocket.send(message)
                    if 'console' in globals():
                        console.print(f"[bold blue]Sent:[/bold blue] {message}")
                    else:
                        print(f"Sent: {message}")
            except Exception as e:
                print(f"Error reading input: {e}")
                break

    async def _listen(self, websocket):
        try:
            async for message in websocket:
                if 'console' in globals():
                    console.print(f"[bold green]Received:[/bold green] {message}")
                else:
                    print(f"Received: {message}")
        except websockets.ConnectionClosed:
            print("Connection closed by server.")
            self.stop_event.set()
        except Exception as e:
            print(f"Error receiving: {e}")
            self.stop_event.set()

    async def run(self, url: str, headers: Optional[List[str]] = None, message: Optional[str] = None, interactive: bool = False, listen: bool = False):
        # Prepare headers
        extra_headers = {}
        if headers:
            for h in headers:
                if ':' in h:
                    k, v = h.split(':', 1)
                    extra_headers[k.strip()] = v.strip()

        print(f"Connecting to {url}...")
        try:
            async with websockets.connect(url, additional_headers=extra_headers) as websocket:
                print("Connected!")

                if message:
                    await websocket.send(message)
                    if 'console' in globals():
                        console.print(f"[bold blue]Sent:[/bold blue] {message}")
                    else:
                        print(f"Sent: {message}")

                    # If just sending a message and not listening/interactive, wait a bit for potential reply then exit
                    if not interactive and not listen:
                        try:
                            reply = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            if 'console' in globals():
                                console.print(f"[bold green]Received:[/bold green] {reply}")
                            else:
                                print(f"Received: {reply}")
                        except asyncio.TimeoutError:
                            pass
                        return

                tasks = []
                # Always listen if interactive or explicitly requested
                if interactive or listen:
                    receive_task = asyncio.create_task(self._listen(websocket))
                    tasks.append(receive_task)

                if interactive:
                    input_task = asyncio.create_task(self._read_stdin(websocket))
                    tasks.append(input_task)

                if tasks:
                    # Setup signal handler to stop gracefully
                    loop = asyncio.get_running_loop()

                    def stop():
                        print("\nDisconnecting...")
                        self.stop_event.set()
                        # We don't cancel tasks immediately here to allow cleanup if needed,
                        # but typically we just set the event.

                    # Handle Ctrl+C
                    try:
                        loop.add_signal_handler(signal.SIGINT, stop)
                    except NotImplementedError:
                         # Windows or non-main thread
                         pass

                    # Wait until stop event
                    await self.stop_event.wait()

                    # Clean up
                    for task in tasks:
                        task.cancel()

                    try:
                         await asyncio.gather(*tasks, return_exceptions=True)
                    except asyncio.CancelledError:
                         pass

        except Exception as e:
            print(f"Connection failed: {e}")
            sys.exit(1)

    async def _handler(self, websocket):
        self.connected_clients.add(websocket)
        remote_addr = websocket.remote_address
        print(f"Client connected: {remote_addr}")
        try:
            async for message in websocket:
                if 'console' in globals():
                    console.print(f"[bold green]Received from {remote_addr}:[/bold green] {message}")
                else:
                    print(f"Received from {remote_addr}: {message}")

                # Broadcast to others
                if len(self.connected_clients) > 1:
                    broadcast_tasks = []
                    for client in self.connected_clients:
                        if client != websocket:
                            broadcast_tasks.append(asyncio.create_task(client.send(f"[{remote_addr}] {message}")))
                    if broadcast_tasks:
                        await asyncio.gather(*broadcast_tasks, return_exceptions=True)

                # Echo back confirmation (optional, but good for testing)
                # await websocket.send(f"Server received: {message}")

        except websockets.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
            print(f"Client disconnected: {remote_addr}")

    async def serve(self, port: int):
        print(f"Starting WebSocket server on port {port}...")
        print("Press Ctrl+C to stop.")

        # Setup signal handler to stop gracefully
        loop = asyncio.get_running_loop()
        def stop():
            print("\nStopping server...")
            self.stop_event.set()

        try:
            loop.add_signal_handler(signal.SIGINT, stop)
        except NotImplementedError:
            pass

        try:
            async with websockets.serve(self._handler, "0.0.0.0", port):
                await self.stop_event.wait()
        except OSError as e:
            print(f"Error starting server: {e}")
            sys.exit(1)

async def run_ws_lab_logic(args):
    manager = WsLabManager()

    # Server Mode
    if getattr(args, 'server', False):
        port = getattr(args, 'port', 8765)
        await manager.serve(port)
        return

    # Client Mode
    url = args.url
    if not url:
        print("Error: URL is required for client mode.", file=sys.stderr)
        print("Use --server to start a server, or provide a URL to connect to.", file=sys.stderr)
        sys.exit(1)

    if not url.startswith("ws://") and not url.startswith("wss://"):
        url = "ws://" + url

    headers = getattr(args, 'header', None)
    message = getattr(args, 'message', None)
    interactive = getattr(args, 'interactive', False)
    listen = getattr(args, 'listen', False)

    await manager.run(url, headers, message, interactive, listen)
