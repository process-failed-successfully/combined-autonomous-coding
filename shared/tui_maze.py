from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, Select, RichLog
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.maze_lab import Maze, MazeGenerator, MazeSolver

class MazeLabTab(Container):
    """Tab for Maze Generation and Solving."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.maze = None
        self.generator = MazeGenerator()
        self.solver = MazeSolver()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Maze Lab[/bold]", classes="welcome-text")

            # Controls
            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Width:")
                    yield Input(placeholder="Width (odd)", value="41", id="maze-width", type="integer")
                with Vertical():
                    yield Label("Height:")
                    yield Input(placeholder="Height (odd)", value="21", id="maze-height", type="integer")
                with Vertical():
                    yield Label("Generator:")
                    yield Select.from_values(["dfs", "prim"], id="maze-gen-algo", value="dfs")
                with Vertical():
                    yield Label("Solver:")
                    yield Select.from_values(["bfs", "dfs"], id="maze-solve-algo", value="bfs")

            with Horizontal(classes="stat-box"):
                yield Button("Generate Maze", id="btn-maze-gen", variant="primary")
                yield Button("Solve Maze", id="btn-maze-solve", variant="success", disabled=True)

            # Canvas
            with VerticalScroll(classes="stat-box", id="maze-canvas-container"):
                yield Label("[bold]Maze View[/bold]")
                yield RichLog(id="maze-log", wrap=False, highlight=False, markup=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-maze-gen":
            self.generate_maze()
        elif event.button.id == "btn-maze-solve":
            self.solve_maze()

    def generate_maze(self) -> None:
        width_val = self.query_one("#maze-width", Input).value
        height_val = self.query_one("#maze-height", Input).value
        algo = self.query_one("#maze-gen-algo", Select).value or "dfs"

        if not width_val or not height_val:
            self.notify("Width and Height required.", severity="error")
            return

        try:
            width = int(width_val)
            height = int(height_val)
        except ValueError:
            self.notify("Invalid dimensions.", severity="error")
            return

        # Clamp size to reasonable limits for TUI
        width = max(5, min(width, 101))
        height = max(5, min(height, 51))

        self.maze = Maze(width, height)
        self.generator.generate(self.maze, algo)

        self.display_maze()
        self.query_one("#btn-maze-solve").disabled = False
        self.notify(f"Maze generated ({width}x{height}) using {algo}.")

    def solve_maze(self) -> None:
        if not self.maze:
            return

        algo = self.query_one("#maze-solve-algo", Select).value or "bfs"

        path = self.solver.solve(self.maze, algo)

        if path:
            # Clone maze for display to avoid permanent modification of base maze
            # Actually, modifying base maze is fine for this session

            # Reset solution path if any
            for y in range(self.maze.height):
                for x in range(self.maze.width):
                    if self.maze.grid[y][x] == self.maze.SOLUTION:
                        self.maze.grid[y][x] = self.maze.PATH

            for x, y in path:
                if (x, y) != self.maze.start and (x, y) != self.maze.end:
                    self.maze.set_cell(x, y, self.maze.SOLUTION)

            self.display_maze()
            self.notify(f"Maze solved using {algo}. Path length: {len(path)}")
        else:
            self.notify("No solution found.", severity="error")

    def display_maze(self) -> None:
        log = self.query_one("#maze-log", RichLog)
        log.clear()
        if self.maze:
            log.write(self.maze.render())
