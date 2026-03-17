from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea, RichLog, DataTable
from textual.reactive import reactive
from shared.brainfuck_lab import BrainfuckInterpreter

class BrainfuckLabTab(Container):
    """Tab for Brainfuck Interpreter."""

    DEFAULT_CSS = """
    BrainfuckLabTab {
        layout: vertical;
        height: 100%;
    }

    .bf-box {
        border: solid $accent;
        padding: 1;
        margin: 1;
        height: auto;
    }

    #bf-code-input {
        height: 10;
    }

    #bf-input-data, #bf-output-log {
        height: 5;
    }

    #bf-memory-table {
        height: 4;
        width: 100%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.interpreter = BrainfuckInterpreter(memory_size=30000)
        self._is_running = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Brainfuck Lab (Interpreter)[/bold]", classes="welcome-text")

            # Code Input
            with Vertical(classes="bf-box"):
                yield Label("Code:")
                yield TextArea(id="bf-code-input", show_line_numbers=True)

            # Input Data
            with Vertical(classes="bf-box"):
                yield Label("Input:")
                yield TextArea(id="bf-input-data", show_line_numbers=False)

            # Controls
            with Horizontal(classes="bf-box"):
                yield Button("Load", id="btn-bf-load", variant="primary")
                yield Button("Step", id="btn-bf-step", variant="warning", disabled=True)
                yield Button("Run", id="btn-bf-run", variant="success", disabled=True)
                yield Button("Reset", id="btn-bf-reset", variant="error")

            # Status
            with Horizontal(classes="bf-box"):
                yield Label("Status: ", id="bf-status-label")
                yield Label("Idle", id="bf-status-value")

            # Memory Tape
            with Vertical(classes="bf-box"):
                yield Label("Memory Tape (Window around Pointer):")
                yield DataTable(id="bf-memory-table")

            # Output
            with Vertical(classes="bf-box"):
                yield Label("Output:")
                yield RichLog(id="bf-output-log", markup=False, wrap=True)

    def on_mount(self) -> None:
        table = self.query_one("#bf-memory-table", DataTable)
        table.add_columns(*[f"{i:02d}" for i in range(21)]) # Show 21 cells
        self.update_ui()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-bf-load":
            self.action_load()
        elif event.button.id == "btn-bf-step":
            self.action_step()
        elif event.button.id == "btn-bf-run":
            self.action_run()
        elif event.button.id == "btn-bf-reset":
            self.action_reset()

    def action_load(self) -> None:
        code = self.query_one("#bf-code-input", TextArea).text
        input_data = self.query_one("#bf-input-data", TextArea).text

        if not code.strip():
            self.notify("Code is empty.", severity="warning")
            return

        try:
            self.interpreter.load(code, input_data)
            self._is_running = True

            self.query_one("#btn-bf-step", Button).disabled = False
            self.query_one("#btn-bf-run", Button).disabled = False
            self.query_one("#btn-bf-load", Button).disabled = True

            self.query_one("#bf-output-log", RichLog).clear()
            self.query_one("#bf-status-value", Label).update("Loaded. Ready to run or step.")

            self.update_ui()
            self.notify("Code loaded.")
        except Exception as e:
            self.notify(f"Load Error: {e}", severity="error")

    def action_step(self) -> None:
        if not self._is_running:
            return

        try:
            continued = self.interpreter.step()
            self.update_ui()

            if not continued:
                self._is_running = False
                self.query_one("#btn-bf-step", Button).disabled = True
                self.query_one("#btn-bf-run", Button).disabled = True
                self.query_one("#bf-status-value", Label).update("Halted (Finished).")
                self.notify("Execution finished.")
            else:
                self.query_one("#bf-status-value", Label).update(f"Stepped. Next instruction: {self.interpreter.code[self.interpreter.ip] if self.interpreter.ip < len(self.interpreter.code) else 'EOF'}")
        except Exception as e:
            self._is_running = False
            self.query_one("#btn-bf-step", Button).disabled = True
            self.query_one("#btn-bf-run", Button).disabled = True
            self.query_one("#bf-status-value", Label).update(f"Error: {e}")
            self.notify(f"Execution Error: {e}", severity="error")

    def action_run(self) -> None:
        if not self._is_running:
            return

        self.query_one("#bf-status-value", Label).update("Running...")
        self.query_one("#btn-bf-step", Button).disabled = True
        self.query_one("#btn-bf-run", Button).disabled = True

        try:
            max_steps = 100000
            steps = 0
            while self.interpreter.step() and steps < max_steps:
                steps += 1

            if steps >= max_steps:
                 self.query_one("#bf-status-value", Label).update("Halted (Max steps exceeded).")
                 self.notify("Max steps exceeded.", severity="warning")
            else:
                 self.query_one("#bf-status-value", Label).update("Halted (Finished).")
                 self.notify("Execution finished.")

            self._is_running = False
            self.update_ui()
        except Exception as e:
            self._is_running = False
            self.query_one("#bf-status-value", Label).update(f"Error: {e}")
            self.notify(f"Execution Error: {e}", severity="error")
            self.update_ui()

    def action_reset(self) -> None:
        self.interpreter.reset()
        self._is_running = False

        self.query_one("#btn-bf-load", Button).disabled = False
        self.query_one("#btn-bf-step", Button).disabled = True
        self.query_one("#btn-bf-run", Button).disabled = True

        self.query_one("#bf-output-log", RichLog).clear()
        self.query_one("#bf-status-value", Label).update("Idle")

        self.update_ui()
        self.notify("Interpreter reset.")

    def update_ui(self) -> None:
        # Update output
        log = self.query_one("#bf-output-log", RichLog)
        log.clear()
        if self.interpreter.output_data:
             log.write(self.interpreter.output_data)

        # Update memory table
        table = self.query_one("#bf-memory-table", DataTable)
        table.clear()

        dp = self.interpreter.dp
        start_idx = max(0, dp - 10)
        end_idx = start_idx + 21
        if end_idx > self.interpreter.memory_size:
             end_idx = self.interpreter.memory_size
             start_idx = max(0, end_idx - 21)

        header_row = [f"Idx {i}" for i in range(start_idx, end_idx)]
        val_row = []
        for i in range(start_idx, end_idx):
            val = f"{self.interpreter.memory[i]:03d}"
            if i == dp:
                val = f"[{val}]" # Mark current pointer
            else:
                val = f" {val} "
            val_row.append(val)

        # Add padding if needed
        while len(header_row) < 21:
             header_row.append("")
             val_row.append("")

        table.add_row(*header_row)
        table.add_row(*val_row)
