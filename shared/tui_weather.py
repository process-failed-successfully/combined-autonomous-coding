from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Button, Select, DataTable, Static
from textual.reactive import reactive
from shared.weather_lab import WeatherLabManager

class WeatherLabTab(Container):
    """Tab for checking weather."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = WeatherLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Weather Lab[/bold]", classes="welcome-text")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Label("City (leave empty for auto):", classes="label")
                yield Input(placeholder="e.g. London, New York", id="weather-city-input")
                yield Select.from_values(["metric", "imperial"], id="weather-units", value="metric")
                yield Button("Fetch Weather", id="btn-fetch-weather", variant="primary")

            # Current Weather Display
            with Container(classes="stat-box", id="weather-current-box"):
                yield Label("[bold]Current Conditions[/bold]")
                yield Static("Enter a location and click Fetch.", id="weather-current-display")

            # Forecast Display
            with Container(classes="stat-box", id="weather-forecast-box"):
                yield Label("[bold]Forecast[/bold]")
                yield DataTable(id="weather-forecast-table")

    def on_mount(self) -> None:
        table = self.query_one("#weather-forecast-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Date", "Condition", "Min Temp", "Max Temp")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-fetch-weather":
            await self.fetch_weather()

    async def fetch_weather(self) -> None:
        city = self.query_one("#weather-city-input", Input).value
        units = self.query_one("#weather-units", Select).value or "metric"

        display = self.query_one("#weather-current-display", Static)
        display.update("Fetching...")

        # Run in thread
        import asyncio
        data = await asyncio.to_thread(self.manager.get_weather, city, units)

        if "error" in data:
            display.update(f"[red]Error: {data['error']}[/red]")
            return

        # Update Current
        loc = data.get("location", {})
        curr = data.get("current_weather", {})

        city_name = loc.get('city') or city or "Unknown"
        region = loc.get('region') or ""
        country = loc.get('country') or ""

        temp = curr.get("temperature")
        wind = curr.get("windspeed")
        code = curr.get("weathercode")
        desc = self.manager.get_weather_code_description(code)

        unit_symbol = "°F" if units == "imperial" else "°C"
        wind_unit = "mph" if units == "imperial" else "km/h"

        text = f"""
        [bold big]{city_name}[/bold big] ({region}, {country})

        Condition: [bold]{desc}[/bold]
        Temp:      [bold]{temp}{unit_symbol}[/bold]
        Wind:      {wind} {wind_unit}
        """
        display.update(text)

        # Update Forecast
        daily = data.get("daily", {})
        table = self.query_one("#weather-forecast-table", DataTable)
        table.clear()

        times = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        codes = daily.get("weathercode", [])

        for i, date in enumerate(times):
            d_desc = self.manager.get_weather_code_description(codes[i])
            table.add_row(
                date,
                d_desc,
                f"{min_temps[i]}{unit_symbol}",
                f"{max_temps[i]}{unit_symbol}"
            )
