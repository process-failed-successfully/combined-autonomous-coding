from typing import Callable, Optional
from pathlib import Path

from aiohttp import web


class HttpServerManager:
    def __init__(self):
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.port: Optional[int] = None
        self.type: Optional[str] = None  # "static" or "echo"
        self._log_callback: Optional[Callable[[str], None]] = None

    def set_log_callback(self, callback: Callable[[str], None]):
        self._log_callback = callback

    def _log(self, message: str):
        if self._log_callback:
            self._log_callback(message)

    async def start_static(self, path: str, port: int):
        await self.stop()

        # Verify path exists
        p = Path(path)
        if not p.exists() or not p.is_dir():
            raise ValueError(f"Invalid directory: {path}")

        app = web.Application()
        # Custom middleware for logging requests
        app.middlewares.append(self._logging_middleware)

        try:
            app.router.add_static('/', str(p), show_index=True)
        except ValueError as e:
            self._log(f"Error adding static path: {e}")
            raise

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '127.0.0.1', port)
        await self.site.start()
        self.port = port
        self.type = "static"
        self._log(f"Static server started on port {port} serving {path}")

    async def start_echo(self, port: int):
        await self.stop()

        async def echo_handler(request):
            text = await request.text()
            data = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "body": text
            }
            # Log specific details handled by middleware mostly, but body here
            if text:
                preview = text[:100] + "..." if len(text) > 100 else text
                self._log(f"Body: {preview}")

            return web.json_response(data)

        app = web.Application()
        app.middlewares.append(self._logging_middleware)
        app.router.add_route('*', '/{tail:.*}', echo_handler)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '127.0.0.1', port)
        await self.site.start()
        self.port = port
        self.type = "echo"
        self._log(f"Echo server started on port {port}")

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

    @web.middleware
    async def _logging_middleware(self, request, handler):
        self._log(f"Request: {request.method} {request.path}")
        try:
            response = await handler(request)
            self._log(f"Response: {response.status}")
            return response
        except Exception as e:
            self._log(f"Error handling request: {e}")
            raise
