import asyncio
import logging
from typing import Optional, Callable, Any
from pathlib import Path
import sys

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    web = None
    AIOHTTP_AVAILABLE = False

# Define a dummy middleware decorator if aiohttp is missing
# to prevent AttributeError during class definition
if not AIOHTTP_AVAILABLE:
    def middleware(func):
        return func
else:
    middleware = web.middleware

class HttpServerManager:
    def __init__(self):
        self.runner: Any = None
        self.site: Any = None
        self.port: Optional[int] = None
        self.type: Optional[str] = None  # "static", "echo", or "upload"
        self._log_callback: Optional[Callable[[str], None]] = None

    def set_log_callback(self, callback: Callable[[str], None]):
        self._log_callback = callback

    def _log(self, message: str):
        if self._log_callback:
            self._log_callback(message)

    @middleware
    async def _logging_middleware(self, request, handler):
        self._log(f"Request: {request.method} {request.path}")
        try:
            response = await handler(request)
            self._log(f"Response: {response.status}")
            return response
        except Exception as e:
            self._log(f"Error handling request: {e}")
            raise

    def create_static_app(self, path: Path) -> Any:
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for this feature")

        app = web.Application()
        # With @web.middleware, the method is already a middleware factory/handler
        app.middlewares.append(self._logging_middleware)
        try:
            app.router.add_static('/', str(path), show_index=True)
        except ValueError as e:
            self._log(f"Error adding static path: {e}")
            raise
        return app

    async def start_static(self, path: str, port: int):
        if not AIOHTTP_AVAILABLE:
            self._log("Error: aiohttp not installed")
            return

        await self.stop()
        p = Path(path)
        if not p.exists() or not p.is_dir():
            raise ValueError(f"Invalid directory: {path}")

        app = self.create_static_app(p)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '127.0.0.1', port)
        await self.site.start()
        self.port = port
        self.type = "static"
        self._log(f"Static server started on port {port} serving {path}")

    def create_echo_app(self) -> Any:
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for this feature")

        async def echo_handler(request):
            text = await request.text()
            data = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "body": text
            }
            if text:
                preview = text[:100] + "..." if len(text) > 100 else text
                self._log(f"Body: {preview}")
            return web.json_response(data)

        app = web.Application()
        app.middlewares.append(self._logging_middleware)
        app.router.add_route('*', '/{tail:.*}', echo_handler)
        return app

    async def start_echo(self, port: int):
        if not AIOHTTP_AVAILABLE:
            self._log("Error: aiohttp not installed")
            return

        await self.stop()
        app = self.create_echo_app()

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '127.0.0.1', port)
        await self.site.start()
        self.port = port
        self.type = "echo"
        self._log(f"Echo server started on port {port}")

    def create_upload_app(self, path: Path) -> Any:
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for this feature")

        # Ensure directory exists
        path.mkdir(parents=True, exist_ok=True)

        async def upload_handler(request):
            if not request.content_type.startswith('multipart/'):
                return web.Response(status=400, text="Content-Type must be multipart/form-data")

            reader = await request.multipart()
            files_saved = []

            while True:
                field = await reader.next()
                if field is None:
                    break

                if field.filename:
                    filename = field.filename
                    filename = Path(filename).name
                    filepath = path / filename
                    size = 0
                    try:
                        with open(filepath, 'wb') as f:
                            while True:
                                chunk = await field.read_chunk()
                                if not chunk:
                                    break
                                f.write(chunk)
                                size += len(chunk)

                        files_saved.append({"filename": filename, "size": size})
                        self._log(f"Saved {filename} ({size} bytes)")
                    except Exception as e:
                        self._log(f"Error saving file {filename}: {e}")
                        return web.Response(status=500, text=f"Error saving file: {e}")

            return web.json_response({"files": files_saved, "directory": str(path)})

        app = web.Application()
        app.middlewares.append(self._logging_middleware)
        app.router.add_post('/', upload_handler)
        return app

    async def start_upload(self, path: str, port: int):
        if not AIOHTTP_AVAILABLE:
            self._log("Error: aiohttp not installed")
            return

        await self.stop()
        p = Path(path)
        app = self.create_upload_app(p)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '127.0.0.1', port)
        await self.site.start()
        self.port = port
        self.type = "upload"
        self._log(f"Upload server started on port {port} saving to {path}")

    async def stop(self):
        if self.site:
            await self.site.stop()
            self.site = None

        if self.runner:
            await self.runner.cleanup()
            self.runner = None

        if self.port:
            self._log(f"Server on port {self.port} stopped.")
            self.port = None
            self.type = None

async def run_http_server_lab_logic(args):
    if not AIOHTTP_AVAILABLE:
        print("Error: aiohttp module is required for HTTP Server Lab.", file=sys.stderr)
        print("Please install it: pip install aiohttp", file=sys.stderr)
        sys.exit(1)

    manager = HttpServerManager()
    manager.set_log_callback(lambda msg: print(f"[HTTP-LAB] {msg}"))

    try:
        if args.action == "serve" or args.action == "static":
            path = getattr(args, "dir", ".")
            port = getattr(args, "port", 8000)
            await manager.start_static(path, port)

        elif args.action == "echo":
            port = getattr(args, "port", 8080)
            await manager.start_echo(port)

        elif args.action == "upload":
            path = getattr(args, "dir", "uploads")
            port = getattr(args, "port", 8081)
            await manager.start_upload(path, port)

        print("Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(3600)

    except asyncio.CancelledError:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        await manager.stop()
