from datetime import date, datetime
from pathlib import Path
from typing import Dict, List
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Static, RichLog
from textual.reactive import reactive
from textual import work
import calendar

from shared.calendar_lab import CalendarLabManager
from shared.task_manager import Task


class CalendarDay(Button):
    """A button representing a day in the calendar."""

    def __init__(self, day: int, year: int, month: int, has_events: bool = False, **kwargs) -> None:
        label = str(day)
        if has_events:
            label = f"{day} •"
        super().__init__(label, **kwargs)
        self.day = day
        self.year = year
        self.month = month
        self.has_events = has_events
        if has_events:
            self.add_class("has-events")


class CalendarTab(Container):
    """Tab for Calendar View."""

    CSS = """
    #calendar-grid {
        layout: grid;
        grid-size: 7;
        grid-gutter: 1;
        height: 1fr;
        margin: 1;
    }

    CalendarDay {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }

    .has-events {
        color: $warning;
        text-style: bold;
    }

    .selected-day {
        background: $primary;
        color: white;
    }

    #calendar-header {
        height: 3;
        align: center middle;
        text-align: center;
        text-style: bold;
        background: $panel;
        margin-bottom: 1;
    }

    #day-header {
        layout: grid;
        grid-size: 7;
        grid-gutter: 1;
        height: 1;
        margin-left: 1;
        margin-right: 1;
    }

    .day-name {
        text-align: center;
        text-style: bold;
        color: $text-muted;
    }

    #calendar-sidebar {
        width: 30%;
        border-left: solid $primary;
        padding: 1;
        height: 100%;
    }
    """

    current_year = reactive(datetime.now().year)
    current_month = reactive(datetime.now().month)
    selected_date = reactive(None)

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CalendarLabManager(project_dir)
        self.events_cache: Dict[int, List[Task]] = {}

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Main Calendar Area
            with Vertical(id="calendar-main"):
                # Header with Navigation
                with Horizontal(id="calendar-controls", classes="stat-box"):
                    yield Button("<<", id="btn-prev-year", variant="default")
                    yield Button("<", id="btn-prev-month", variant="default")
                    yield Label("", id="lbl-month-year", classes="calendar-title")
                    yield Button(">", id="btn-next-month", variant="default")
                    yield Button(">>", id="btn-next-year", variant="default")
                    yield Button("Today", id="btn-today", variant="primary")

                # Day Names Header
                with Container(id="day-header"):
                    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                        yield Label(day, classes="day-name")

                # Calendar Grid
                yield Container(id="calendar-grid")

            # Sidebar for Details
            with Vertical(id="calendar-sidebar"):
                yield Label("[bold]Day Details[/bold]", id="lbl-details-header")
                yield Label("Select a day to view tasks.", id="lbl-details-sub")
                yield RichLog(id="calendar-details-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.update_calendar()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-prev-month":
            self.change_month(-1)
        elif bid == "btn-next-month":
            self.change_month(1)
        elif bid == "btn-prev-year":
            self.change_year(-1)
        elif bid == "btn-next-year":
            self.change_year(1)
        elif bid == "btn-today":
            now = datetime.now()
            self.current_year = now.year
            self.current_month = now.month
            self.update_calendar()
        elif isinstance(event.button, CalendarDay):
            self.select_day(event.button)

    def change_month(self, delta: int) -> None:
        new_month = self.current_month + delta
        new_year = self.current_year

        while new_month > 12:
            new_month -= 12
            new_year += 1
        while new_month < 1:
            new_month += 12
            new_year -= 1

        self.current_year = new_year
        self.current_month = new_month
        self.update_calendar()

    def change_year(self, delta: int) -> None:
        self.current_year += delta
        self.update_calendar()

    def update_calendar(self) -> None:
        # Update Header
        month_name = calendar.month_name[self.current_month]
        self.query_one("#lbl-month-year", Label).update(f"{month_name} {self.current_year}")

        # Run worker to fetch events (avoids freezing UI)
        self._fetch_events_worker()

    @work(exclusive=True, thread=True)
    def _fetch_events_worker(self) -> None:
        # Capture current state
        year = self.current_year
        month = self.current_month

        events = self.manager.get_events_for_month(year, month)

        # Schedule update on main thread
        self.app.call_from_thread(self._render_grid, events, year, month)

    def _render_grid(self, events: Dict[int, List[Task]], year: int, month: int) -> None:
        # Verify we are still looking at the same month (in case user navigated away fast)
        if year != self.current_year or month != self.current_month:
            return

        self.events_cache = events
        grid = self.query_one("#calendar-grid", Container)
        grid.remove_children()

        matrix = self.manager.get_month_matrix(year, month)

        today = datetime.now().date()

        for week in matrix:
            for day in week:
                if day is None:
                    grid.mount(Static("", classes="empty-cell"))
                else:
                    has_events = day in self.events_cache
                    btn = CalendarDay(day, year, month, has_events=has_events)

                    if (year == today.year and
                            month == today.month and
                            day == today.day):
                        btn.add_class("today-cell")

                    grid.mount(btn)

    def select_day(self, button: CalendarDay) -> None:
        # Highlight logic (remove class from others, add to this)
        for child in self.query_one("#calendar-grid").children:
            child.remove_class("selected-day")
        button.add_class("selected-day")

        target_date = date(self.current_year, self.current_month, button.day)
        self.show_details(target_date)

    def show_details(self, target_date: date) -> None:
        header = self.query_one("#lbl-details-header", Label)
        header.update(f"[bold]{target_date.strftime('%A, %B %d, %Y')}[/bold]")

        sub = self.query_one("#lbl-details-sub", Label)
        log = self.query_one("#calendar-details-log", RichLog)
        log.clear()

        day_num = target_date.day
        tasks = self.events_cache.get(day_num, [])

        if not tasks:
            sub.update("No tasks due today.")
            return

        sub.update(f"{len(tasks)} tasks due.")

        for task in tasks:
            source_color = "blue"
            if task.source == "jira":
                source_color = "cyan"
            elif task.source == "sprint":
                source_color = "magenta"
            elif task.source == "github":
                source_color = "white"

            log.write(f"[{source_color}]{task.source.upper()}[/{source_color}] [bold]{task.id}[/bold]")
            log.write(f"  {task.title}")
            log.write(f"  Status: {task.status}")
            if task.priority:
                p_color = "green"
                if task.priority.lower() == "high":
                    p_color = "red"
                elif task.priority.lower() == "medium":
                    p_color = "yellow"
                log.write(f"  Priority: [{p_color}]{task.priority}[/{p_color}]")
            log.write("")
