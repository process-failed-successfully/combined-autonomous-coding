from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, TextArea, DataTable, RichLog
from textual import on
from shared.matrix_lab import MatrixLabManager

class MatrixLabTab(Container):
    """Tab for Matrix Arithmetic."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = MatrixLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Matrix Lab[/bold]", classes="welcome-text")

            # Input Area
            with Horizontal(id="matrix-input-area"):
                with Vertical(classes="stat-box matrix-box"):
                    yield Label("Matrix A")
                    yield TextArea(id="input-matrix-a", language="json")

                with Vertical(classes="stat-box matrix-box"):
                    yield Label("Matrix B")
                    yield TextArea(id="input-matrix-b", language="json")

            # Controls
            with Horizontal(classes="stat-box", id="matrix-controls"):
                yield Button("A + B", id="btn-matrix-add", variant="primary")
                yield Button("A - B", id="btn-matrix-sub", variant="primary")
                yield Button("A * B", id="btn-matrix-mul", variant="primary")
                yield Button("Det(A)", id="btn-matrix-det-a", variant="warning")
                yield Button("Det(B)", id="btn-matrix-det-b", variant="warning")
                yield Button("Trans(A)", id="btn-matrix-trans-a", variant="default")
                yield Button("Trans(B)", id="btn-matrix-trans-b", variant="default")

            # Result Area
            with Vertical(id="matrix-result-container"):
                yield Label("[bold]Result[/bold]")
                yield RichLog(id="matrix-log", wrap=True, highlight=True, markup=True)
                yield DataTable(id="matrix-result-table")

    def on_mount(self) -> None:
        table = self.query_one("#matrix-result-table", DataTable)
        table.cursor_type = "none" # Read-only view

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-matrix-add":
            self.perform_op("add")
        elif bid == "btn-matrix-sub":
            self.perform_op("sub")
        elif bid == "btn-matrix-mul":
            self.perform_op("mul")
        elif bid == "btn-matrix-det-a":
            self.perform_op("det_a")
        elif bid == "btn-matrix-det-b":
            self.perform_op("det_b")
        elif bid == "btn-matrix-trans-a":
            self.perform_op("trans_a")
        elif bid == "btn-matrix-trans-b":
            self.perform_op("trans_b")

    def perform_op(self, op: str) -> None:
        text_a = self.query_one("#input-matrix-a", TextArea).text
        text_b = self.query_one("#input-matrix-b", TextArea).text
        log = self.query_one("#matrix-log", RichLog)
        table = self.query_one("#matrix-result-table", DataTable)

        log.clear()
        table.clear(columns=True)

        try:
            mat_a = self.manager.parse_matrix(text_a) if text_a.strip() else []
            mat_b = self.manager.parse_matrix(text_b) if text_b.strip() else []

            result = None
            scalar_result = None

            if op == "add":
                result = self.manager.add(mat_a, mat_b)
                log.write("[bold green]Result: A + B[/bold green]")
            elif op == "sub":
                result = self.manager.subtract(mat_a, mat_b)
                log.write("[bold green]Result: A - B[/bold green]")
            elif op == "mul":
                result = self.manager.multiply(mat_a, mat_b)
                log.write("[bold green]Result: A * B[/bold green]")
            elif op == "det_a":
                scalar_result = self.manager.determinant(mat_a)
                log.write(f"[bold green]Determinant(A): {scalar_result}[/bold green]")
            elif op == "det_b":
                scalar_result = self.manager.determinant(mat_b)
                log.write(f"[bold green]Determinant(B): {scalar_result}[/bold green]")
            elif op == "trans_a":
                result = self.manager.transpose(mat_a)
                log.write("[bold green]Transpose(A)[/bold green]")
            elif op == "trans_b":
                result = self.manager.transpose(mat_b)
                log.write("[bold green]Transpose(B)[/bold green]")

            # Display Result
            if result is not None:
                # Populate Table
                if result and result[0]:
                    cols = len(result[0])
                    # Add columns 0, 1, 2...
                    for i in range(cols):
                        table.add_column(str(i))

                    for row in result:
                        table.add_row(*[f"{x:.2f}" for x in row])
                else:
                    log.write("Result is empty.")

        except Exception as e:
            log.write(f"[bold red]Error: {e}[/bold red]")
