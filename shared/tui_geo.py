from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, TabbedContent, TabPane
from shared.geo_lab import GeoLabManager


class GeoLabTab(Container):
    """Tab for Geolocation utilities."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = GeoLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Geo Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Locate Pane
                with TabPane("Locate IP/Domain"):
                    with Horizontal(classes="stat-box"):
                        yield Input(placeholder="IP address or domain...", id="geo-query-input")
                        yield Button("Locate", id="btn-geo-locate", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Results[/bold]")
                        yield RichLog(id="geo-locate-log", wrap=True, highlight=True, markup=True)

                # Distance Pane
                with TabPane("Calculate Distance"):
                    with Vertical(classes="stat-box"):
                        yield Label("Point 1 (lat,lon):")
                        yield Input(placeholder="e.g. 40.7128,-74.0060", id="geo-dist-p1")
                        yield Label("Point 2 (lat,lon):")
                        yield Input(placeholder="e.g. 51.5074,-0.1278", id="geo-dist-p2")
                        yield Button("Calculate", id="btn-geo-dist", variant="warning")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="geo-dist-log", wrap=True, highlight=True, markup=True)

                # Map Pane
                with TabPane("Google Maps Link"):
                    with Horizontal(classes="stat-box"):
                        yield Input(placeholder="Coordinates (lat,lon)...", id="geo-map-input")
                        yield Button("Generate Link", id="btn-geo-map", variant="success")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Map Link[/bold]")
                        yield RichLog(id="geo-map-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-geo-locate":
            self.locate_query()
        elif event.button.id == "btn-geo-dist":
            self.calculate_distance()
        elif event.button.id == "btn-geo-map":
            self.generate_map_link()

    def locate_query(self) -> None:
        query = self.query_one("#geo-query-input", Input).value.strip()
        log = self.query_one("#geo-locate-log", RichLog)

        log.clear()

        if not query:
            self.notify("Query required.", severity="error")
            return

        log.write(f"Locating '{query}'...")

        import asyncio
        asyncio.create_task(self._async_locate(query, log))

    async def _async_locate(self, query: str, log: RichLog) -> None:
        import asyncio
        try:
            result = await asyncio.to_thread(self.manager.locate, query)
            log.clear()
            if result.get("status") == "success":
                lat = result.get('lat', 0.0)
                lon = result.get('lon', 0.0)
                log.write("[bold green]Success[/bold green]")
                log.write(f"IP: {result.get('query')}")
                log.write(f"Location: {result.get('city')}, {result.get('regionName')}, {result.get('country')}")
                log.write(f"Coordinates: {lat}, {lon}")
                log.write(f"ISP: {result.get('isp')}")
                log.write(f"Timezone: {result.get('timezone')}")

                map_url = self.manager.map_url(float(lat), float(lon))
                log.write(f"Map: {map_url}")

                self.notify("Location found.")
            else:
                log.write(f"[bold red]Failed:[/bold red] {result.get('message')}")
                self.notify("Location failed.", severity="error")
        except Exception as e:
            log.clear()
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Error locating: {e}", severity="error")

    def calculate_distance(self) -> None:
        p1_str = self.query_one("#geo-dist-p1", Input).value.strip()
        p2_str = self.query_one("#geo-dist-p2", Input).value.strip()
        log = self.query_one("#geo-dist-log", RichLog)

        log.clear()

        if not p1_str or not p2_str:
            self.notify("Both points required.", severity="error")
            return

        try:
            p1 = p1_str.split(',')
            p2 = p2_str.split(',')
            lat1, lon1 = float(p1[0]), float(p1[1])
            lat2, lon2 = float(p2[0]), float(p2[1])

            dist = self.manager.calculate_distance(lat1, lon1, lat2, lon2)
            log.write("[bold green]Distance Calculated[/bold green]")
            log.write(f"From: {lat1}, {lon1}")
            log.write(f"To:   {lat2}, {lon2}")
            log.write(f"Result: {dist['km']} km ({dist['miles']} miles)")
            self.notify("Distance calculated.")
        except (ValueError, IndexError):
            log.write("[bold red]Error:[/bold red] Coordinates must be in 'lat,lon' format (e.g., 40.7128,-74.0060).")
            self.notify("Invalid coordinate format.", severity="error")
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Error calculating distance: {e}", severity="error")

    def generate_map_link(self) -> None:
        p_str = self.query_one("#geo-map-input", Input).value.strip()
        log = self.query_one("#geo-map-log", RichLog)

        log.clear()

        if not p_str:
            self.notify("Coordinates required.", severity="error")
            return

        try:
            p = p_str.split(',')
            lat, lon = float(p[0]), float(p[1])
            link = self.manager.map_url(lat, lon)
            log.write("[bold green]Map Link Generated[/bold green]")
            log.write(link)
            self.notify("Map link generated.")
        except (ValueError, IndexError):
            log.write("[bold red]Error:[/bold red] Coordinates must be in 'lat,lon' format.")
            self.notify("Invalid coordinate format.", severity="error")
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Error generating link: {e}", severity="error")
