from pathlib import Path
from datetime import date, datetime
import asyncio
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, DataTable, Input, TextArea, ListView, ListItem, Static, Select
from textual import on
from textual.reactive import reactive

from shared.day_planner import DayPlannerManager, TimeBlock
from shared.task_manager import Task

class DayPlannerTab(Container):
    """
    Day Planner Tab: Schedule tasks and manage time blocks.
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = DayPlannerManager(project_dir)
        self.current_date = date.today()
        self.selected_task: Optional[Task] = None
        self.selected_block: Optional[str] = None # block_id

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Unscheduled Tasks
            with Vertical(id="dp-task-pool", classes="stat-box"):
                yield Label("[bold]Task Pool[/bold]")
                yield Button("Refresh Tasks", id="btn-dp-refresh-tasks", variant="default")
                yield ListView(id="dp-task-list")
                yield Button("Schedule Selected", id="btn-dp-schedule-task", variant="primary", disabled=True)
                yield Button("Auto Schedule", id="btn-dp-auto-schedule", variant="warning")

            # Center Pane: Timeline (Day View)
            with Vertical(id="dp-timeline-container", classes="stat-box"):
                with Horizontal():
                    yield Label(f"[bold]{self.current_date.strftime('%Y-%m-%d')}[/bold]", id="lbl-dp-date")
                    yield Button("Today", id="btn-dp-today", variant="default", classes="small-btn")

                yield DataTable(id="dp-timeline-table")

                with Horizontal():
                    yield Input(placeholder="09:00", id="dp-time-input", classes="small-input")
                    yield Input(placeholder="60", id="dp-duration-input", classes="small-input")
                    yield Input(placeholder="Title (if no task)...", id="dp-title-input")
                    yield Button("Add Block", id="btn-dp-add-block", variant="success")

            # Right Pane: Block Details & Notes
            with Vertical(id="dp-details-container"):
                # Block Details
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Block Details[/bold]")
                    yield Label("Select a block to view details.", id="lbl-dp-block-details")
                    yield Button("Start Focus", id="btn-dp-start-focus", variant="primary", disabled=True)
                    yield Button("Remove Block", id="btn-dp-remove-block", variant="error", disabled=True)

                # Daily Notes
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Daily Notes[/bold]")
                    yield TextArea(id="dp-notes-editor")
                    yield Button("Save Notes", id="btn-dp-save-notes", variant="success")

    def on_mount(self) -> None:
        # Init Timeline Table
        table = self.query_one("#dp-timeline-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Time", "Duration", "Activity")

        self.refresh_view()

    def refresh_view(self) -> None:
        self.load_tasks()
        self.load_timeline()
        self.load_notes()

    def load_tasks(self) -> None:
        tasks = self.manager.get_unscheduled_tasks(self.current_date)
        list_view = self.query_one("#dp-task-list", ListView)
        list_view.clear()

        for t in tasks:
            label = f"[{t.priority}] {t.title}"
            item = ListItem(Label(label))
            item.task_data = t # Monkey-patch task data
            list_view.append(item)

    def load_timeline(self) -> None:
        plan = self.manager.get_plan(self.current_date)
        table = self.query_one("#dp-timeline-table", DataTable)
        table.clear()

        for block in plan.blocks:
            table.add_row(
                block.start_time,
                f"{block.duration}m",
                block.title,
                key=block.id
            )

    def load_notes(self) -> None:
        plan = self.manager.get_plan(self.current_date)
        editor = self.query_one("#dp-notes-editor", TextArea)
        editor.text = plan.notes

    # --- Event Handlers ---

    @on(ListView.Selected, "#dp-task-list")
    def on_task_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "task_data"):
            self.selected_task = event.item.task_data
            self.query_one("#btn-dp-schedule-task").disabled = False
            # Pre-fill title
            self.query_one("#dp-title-input", Input).value = self.selected_task.title

    @on(DataTable.RowSelected, "#dp-timeline-table")
    def on_block_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_block = event.row_key.value
        self.update_block_details()

    def update_block_details(self) -> None:
        if not self.selected_block:
            return

        plan = self.manager.get_plan(self.current_date)
        block = next((b for b in plan.blocks if b.id == self.selected_block), None)

        if block:
            details = f"Title: {block.title}\nTime: {block.start_time} ({block.duration} min)\nTask ID: {block.task_id or 'N/A'}"
            self.query_one("#lbl-dp-block-details", Label).update(details)
            self.query_one("#btn-dp-remove-block").disabled = False
            self.query_one("#btn-dp-start-focus").disabled = False
        else:
            self.query_one("#lbl-dp-block-details", Label).update("Block not found.")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id

        if bid == "btn-dp-refresh-tasks":
            self.load_tasks()

        elif bid == "btn-dp-schedule-task":
            if self.selected_task:
                await self.add_block(use_selected_task=True)

        elif bid == "btn-dp-add-block":
            await self.add_block(use_selected_task=False)

        elif bid == "btn-dp-remove-block":
            self.remove_block()

        elif bid == "btn-dp-save-notes":
            self.save_notes()

        elif bid == "btn-dp-auto-schedule":
            self.auto_schedule()

        elif bid == "btn-dp-start-focus":
            self.start_focus()

    async def add_block(self, use_selected_task: bool) -> None:
        time_val = self.query_one("#dp-time-input", Input).value
        dur_val = self.query_one("#dp-duration-input", Input).value
        title_val = self.query_one("#dp-title-input", Input).value

        if not time_val or not dur_val:
            self.notify("Time and Duration required.", severity="error")
            return

        try:
            duration = int(dur_val)
        except ValueError:
            self.notify("Duration must be a number.", severity="error")
            return

        if not title_val:
            self.notify("Title required.", severity="error")
            return

        task_id = self.selected_task.id if use_selected_task and self.selected_task else None

        # Add block
        block_id = self.manager.add_block(self.current_date, time_val, duration, title_val, task_id)

        if block_id:
            self.notify("Block added.")
            self.refresh_view()
            # Clear inputs
            self.query_one("#dp-title-input", Input).value = ""
            self.selected_task = None
            self.query_one("#btn-dp-schedule-task").disabled = True
        else:
            self.notify("Failed to add block (Overlap or Invalid Time).", severity="error")

    def remove_block(self) -> None:
        if not self.selected_block:
            return

        if self.manager.remove_block(self.current_date, self.selected_block):
            self.notify("Block removed.")
            self.selected_block = None
            self.query_one("#lbl-dp-block-details", Label).update("Select a block.")
            self.query_one("#btn-dp-remove-block").disabled = True
            self.query_one("#btn-dp-start-focus").disabled = True
            self.refresh_view()

    def save_notes(self) -> None:
        notes = self.query_one("#dp-notes-editor", TextArea).text
        self.manager.update_notes(self.current_date, notes)
        self.notify("Notes saved.")

    def auto_schedule(self) -> None:
        count = self.manager.auto_schedule(self.current_date)
        if count > 0:
            self.notify(f"Auto-scheduled {count} tasks.")
            self.refresh_view()
        else:
            self.notify("Could not auto-schedule any tasks (no slots or no tasks).", severity="warning")

    def start_focus(self) -> None:
        if not self.selected_block:
            return

        # Switch to Focus Tab (ProductivityTab)
        # We need to access the main App to switch tabs and populate data
        try:
            tabs = self.app.query_one("TabbedContent")
            tabs.active = "tab-focus"

            # Find productivity tab
            # It might be nested in the content
            # This relies on the structure of AgentTUI
            # For robust integration, we might trigger an event or use a shared state.
            # But direct query often works if widgets are unique ID.

            # Note: ProductivityTab uses Select for task. We should try to pre-select it.
            # But the block ID isn't the task ID.

            plan = self.manager.get_plan(self.current_date)
            block = next((b for b in plan.blocks if b.id == self.selected_block), None)

            if block and block.task_id:
                # We can try to notify the user to select the task, or try to set it.
                self.notify(f"Starting focus for: {block.title}")
            else:
                self.notify(f"Starting focus session.", severity="information")

        except Exception as e:
            self.notify(f"Could not switch tab: {e}", severity="error")
