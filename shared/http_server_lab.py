import sys
import asyncio
import logging
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from aiohttp import web

class HttpServerManager:
    """
    Manages a simple HTTP server (static files or echo) in a separate thread.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self._server_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self.is_running = False
        self.log_callback: Optional[Callable[[str], None]] = None

    def start_server(self, port: int, directory: Optional[str] = None, mode: str = "static", callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Starts the server in a separate thread.

        Args:
            port: Port to listen on (localhost).
            directory: Directory to serve (relative to project_dir or absolute).
            mode: 'static' or 'echo'.
            callback: Function to call with log messages.
        """
        if self.is_running:
            if callback:
                callback("Server is already running.")
            return

        self.log_callback = callback
        self._server_thread = threading.Thread(
            target=self._run_server,
            args=(port, directory, mode),
            daemon=True
        )
        self._server_thread.start()

    def stop_server(self) -> None:
        """
        Stops the server gracefully.
        """
        if self._loop and self.is_running:
            asyncio.run_coroutine_threadsafe(self._stop(), self._loop)
            if self._server_thread:
                self._server_thread.join(timeout=2.0)
            self.is_running = False
            if self.log_callback:
                self.log_callback("Server stopped.")

    def _run_server(self, port: int, directory: Optional[str], mode: str) -> None:
        """
        Internal method to run the server logic in the thread.
        """
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            app = web.Application()

            # Add logging middleware
            app.middlewares.append(self._logging_middleware)

            if mode == "static":
                target_dir = self.project_dir
                if directory:
                    p = Path(directory)
                    if p.is_absolute():
                        target_dir = p
                    else:
                        target_dir = self.project_dir / directory

                if not target_dir.exists() or not target_dir.is_dir():
                    if self.log_callback:
                        self.log_callback(f"Error: Directory '{target_dir}' does not exist.")
                    return

                app.router.add_static('/', path=target_dir, show_index=True)
                if self.log_callback:
                    self.log_callback(f"Serving files from: {target_dir}")

            elif mode == "echo":
                app.router.add_route('*', '/{tail:.*}', self._echo_handler)
                if self.log_callback:
                    self.log_callback("Echo server active on all routes.")

            self._runner = web.AppRunner(app)
            self._loop.run_until_complete(self._runner.setup())

            # Bind to localhost only for security
            self._site = web.TCPSite(self._runner, '127.0.0.1', port)

            try:
                self._loop.run_until_complete(self._site.start())
                self.is_running = True
                if self.log_callback:
                    self.log_callback(f"Server started on http://127.0.0.1:{port}")
                self._loop.run_forever()
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"Server error: {e}")
            finally:
                self.is_running = False
                # Clean up runner if loop stops unexpectedly
                if self._runner:
                     self._loop.run_until_complete(self._runner.cleanup())
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Thread error: {e}")

    async def _stop(self) -> None:
        """
        Async stop logic.
        """
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        if self._loop:
            self._loop.stop()

    async def _echo_handler(self, request: web.Request) -> web.Response:
        """
        Handles requests in echo mode.
        """
        try:
            body = await request.text()
        except Exception:
            body = "<binary or invalid text>"

        data = {
            "method": request.method,
            "path": request.path,
            "query": dict(request.query),
            "headers": dict(request.headers),
            "body": body,
            "remote": request.remote
        }
        return web.json_response(data)

    @web.middleware
    async def _logging_middleware(self, request: web.Request, handler: Callable) -> web.StreamResponse:
        """
        Middleware to log requests.
        """
        if self.log_callback:
            self.log_callback(f"→ {request.method} {request.path}")

        try:
            response = await handler(request)
            if self.log_callback:
                # Basic status info
                content_len = response.content_length if response.content_length is not None else 0
                self.log_callback(f"← {response.status} ({content_len} bytes)")
            return response
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"← Error: {e}")
            raise
