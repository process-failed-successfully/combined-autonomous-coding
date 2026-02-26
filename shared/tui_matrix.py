from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, RichLog, Select
from textual import on
from shared.matrix_lab import MatrixLabManager

class MatrixLabTab(Container):
    """Tab for Matrix Laboratory operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = MatrixLabManager()
        self.matrix_a = []
        self.matrix_b = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Matrix Lab[/bold]", classes="welcome-text")

            # Input Section
            with Horizontal(classes="stat-box"):
                with Vertical(id="matrix-input-a"):
                    yield Label("Matrix A (e.g. 1,2;3,4)")
                    yield Input(placeholder="Rows separated by semicolon, cols by comma", id="input-matrix-a")
                    yield Button("Set A", id="btn-set-a", variant="primary")
                    yield RichLog(id="display-matrix-a", height=5, markup=True)

                with Vertical(id="matrix-input-b"):
                    yield Label("Matrix B (e.g. 5,6;7,8)")
                    yield Input(placeholder="Rows separated by semicolon, cols by comma", id="input-matrix-b")
                    yield Button("Set B", id="btn-set-b", variant="primary")
                    yield RichLog(id="display-matrix-b", height=5, markup=True)

            # Operations Section
            with Container(classes="stat-box"):
                yield Label("[bold]Operations[/bold]")
                with Horizontal():
                    yield Button("A + B", id="btn-add", variant="default")
                    yield Button("A - B", id="btn-sub", variant="default")
                    yield Button("A * B", id="btn-mul", variant="default")
                    yield Button("Det(A)", id="btn-det-a", variant="warning")
                    yield Button("Transpose(A)", id="btn-trans-a", variant="warning")

                with Horizontal():
                    yield Input(placeholder="Scalar...", id="input-scalar", classes="small-input")
                    yield Button("Scale A", id="btn-scale-a", variant="default")

            # Result Section
            with VerticalScroll(id="matrix-result-container", classes="stat-box"):
                yield Label("[bold]Result[/bold]")
                yield RichLog(id="matrix-output", wrap=True, highlight=False, markup=True)

    def parse_matrix(self, text: str):
        try:
            rows = text.strip().split(';')
            matrix = []
            for r in rows:
                if not r.strip():
                    continue
                cols = [float(x.strip()) for x in r.split(',')]
                matrix.append(cols)
            # Validate consistency
            if not matrix:
                return []
            cols_len = len(matrix[0])
            for r in matrix:
                if len(r) != cols_len:
                    raise ValueError("Inconsistent row lengths")
            return matrix
        except Exception as e:
            self.notify(f"Invalid matrix format: {e}", severity="error")
            return []

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        op = event.button.id
        if op == "btn-set-a":
            text = self.query_one("#input-matrix-a", Input).value
            self.matrix_a = self.parse_matrix(text)
            self.display_matrix("#display-matrix-a", self.matrix_a, "A")
        elif op == "btn-set-b":
            text = self.query_one("#input-matrix-b", Input).value
            self.matrix_b = self.parse_matrix(text)
            self.display_matrix("#display-matrix-b", self.matrix_b, "B")
        elif op == "btn-add":
            self.perform_op("add")
        elif op == "btn-sub":
            self.perform_op("sub")
        elif op == "btn-mul":
            self.perform_op("mul")
        elif op == "btn-det-a":
            self.perform_op("det_a")
        elif op == "btn-trans-a":
            self.perform_op("trans_a")
        elif op == "btn-scale-a":
            self.perform_op("scale_a")

    def display_matrix(self, widget_id: str, matrix, label: str):
        log = self.query_one(widget_id, RichLog)
        log.clear()
        if not matrix:
            log.write(f"{label}: [Empty]")
        else:
            fmt = self.manager.format_matrix(matrix)
            log.write(f"[bold]{label}:[/bold]\n{fmt}")

    def perform_op(self, op: str):
        out = self.query_one("#matrix-output", RichLog)
        out.clear()

        try:
            result = None
            msg = ""

            if op == "add":
                if not self.matrix_a or not self.matrix_b:
                    self.notify("Both A and B required.", severity="error")
                    return
                result = self.manager.add(self.matrix_a, self.matrix_b)
                msg = "A + B ="

            elif op == "sub":
                if not self.matrix_a or not self.matrix_b:
                    self.notify("Both A and B required.", severity="error")
                    return
                result = self.manager.subtract(self.matrix_a, self.matrix_b)
                msg = "A - B ="

            elif op == "mul":
                if not self.matrix_a or not self.matrix_b:
                    self.notify("Both A and B required.", severity="error")
                    return
                result = self.manager.multiply(self.matrix_a, self.matrix_b)
                msg = "A * B ="

            elif op == "det_a":
                if not self.matrix_a:
                    self.notify("Matrix A required.", severity="error")
                    return
                val = self.manager.determinant(self.matrix_a)
                out.write(f"Determinant(A) = {val}")
                return

            elif op == "trans_a":
                if not self.matrix_a:
                    self.notify("Matrix A required.", severity="error")
                    return
                result = self.manager.transpose(self.matrix_a)
                msg = "Transpose(A) ="

            elif op == "scale_a":
                if not self.matrix_a:
                    self.notify("Matrix A required.", severity="error")
                    return
                s_text = self.query_one("#input-scalar", Input).value
                try:
                    scalar = float(s_text)
                except:
                    self.notify("Invalid scalar.", severity="error")
                    return
                result = self.manager.scale(self.matrix_a, scalar)
                msg = f"Scale A by {scalar} ="

            if result is not None:
                fmt = self.manager.format_matrix(result)
                out.write(f"[bold]{msg}[/bold]\n{fmt}")

        except Exception as e:
            out.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Operation failed: {e}", severity="error")
