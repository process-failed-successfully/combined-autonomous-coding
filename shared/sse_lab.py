import argparse
import sys
import aiohttp
import asyncio
try:
    from rich.console import Console
    console = Console()
    print_rich = console.print
except ImportError:
    print_rich = print

class SSELabManager:
    """Manages Server-Sent Events interactions (Client)."""

    async def listen(self, url: str, headers: dict = None):
        if not headers:
            headers = {}
        headers["Accept"] = "text/event-stream"
        headers["Cache-Control"] = "no-cache"

        print(f"Connecting to SSE endpoint {url}...")
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Error: Server returned status {response.status}")
                        return

                    print("Connected. Listening for events... (Press Ctrl+C to stop)")

                    async for line in response.content:
                        line_text = line.decode('utf-8').strip()
                        if not line_text:
                            continue

                        if line_text.startswith("data: "):
                            data = line_text[6:]
                            print_rich(f"[bold green]Data:[/bold green] {data}")
                        elif line_text.startswith("event: "):
                            event = line_text[7:]
                            print_rich(f"[bold blue]Event:[/bold blue] {event}")
                        elif line_text.startswith("id: "):
                            id = line_text[4:]
                            print_rich(f"[dim]ID:[/dim] {id}")
                        elif line_text.startswith("retry: "):
                            retry = line_text[7:]
                            print_rich(f"[dim]Retry:[/dim] {retry}")
                        else:
                            print_rich(f"[dim]{line_text}[/dim]")
        except asyncio.CancelledError:
            print("\nDisconnected.")
        except Exception as e:
            print(f"Error: {e}")

async def run_sse_lab_logic(args: argparse.Namespace):
    if getattr(args, 'tui', False):
        from main import run_tui
        run_tui(args, start_tab='sse')
        return

    url = args.url
    if not url:
        print("Error: URL is required.", file=sys.stderr)
        sys.exit(1)

    headers_dict = {}
    if getattr(args, 'header', None):
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                headers_dict[k.strip()] = v.strip()

    manager = SSELabManager()

    try:
        await manager.listen(url, headers_dict)
    except KeyboardInterrupt:
        print("\nStopped.")
