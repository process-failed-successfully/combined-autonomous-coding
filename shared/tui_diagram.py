from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Input, Select, RadioButton, RadioSet, Static
from textual import on, events
from rich.text import Text
from rich.style import Style

from shared.diagram_lab import DiagramLabManager

class DiagramCanvas(Static):
    """
    A widget that renders the ASCII diagram and handles input.
    """
    def __init__(self, manager: DiagramLabManager, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.cursor_x = 0
        self.cursor_y = 0
        self.can_focus = True  # Enable focus to receive key events

    def on_mount(self) -> None:
        self.update_content()

    def update_content(self) -> None:
        # Render canvas text
        lines = ["".join(row) for row in self.manager.canvas]

        # Overlay cursor
        if 0 <= self.cursor_y < len(lines):
            line = list(lines[self.cursor_y])
            if 0 <= self.cursor_x < len(line):
                # Using a special style/char for cursor?
                # For now, let's just highlight it by using Rich Text
                pass

        # Build Rich Text object
        text = Text()
        for y, line_str in enumerate(lines):
            if y == self.cursor_y:
                # Highlight cursor char
                if 0 <= self.cursor_x < len(line_str):
                    pre = line_str[:self.cursor_x]
                    char = line_str[self.cursor_x]
                    post = line_str[self.cursor_x+1:]
                    text.append(pre)
                    text.append(char, style="reverse")
                    text.append(post + "\n")
                else:
                    text.append(line_str + "\n")
            else:
                text.append(line_str + "\n")

        self.update(text)

class DiagramLabTab(Container):
    """
    Interactive ASCII Diagram Editor.
    """

    TOOLS = {
        "cursor": "Cursor (Move)",
        "pen": "Pen (Type)",
        "line": "Line (Enter start/end)",
        "box": "Box (Enter start/end)",
        "text": "Text (Enter to type)",
        "eraser": "Eraser (Space to clear)"
    }

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = DiagramLabManager(80, 24)
        self.current_tool = "cursor"
        self.current_style = "light"

        # State for multi-step tools (line, box)
        self.start_pos = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Sidebar
            with Vertical(id="diagram-sidebar", classes="stat-box"):
                yield Label("[bold]Tools[/bold]")
                with RadioSet(id="diagram-tool-select"):
                    for tool, desc in self.TOOLS.items():
                        yield RadioButton(desc, id=f"tool-{tool}", value=(tool=="cursor"))

                yield Label("[bold]Style[/bold]")
                styles = [(k, k) for k in self.manager.STYLES.keys()]
                yield Select(styles, value="light", id="diagram-style-select", allow_blank=False)

                yield Label("[bold]Actions[/bold]")
                yield Button("Clear Canvas", id="btn-diagram-clear", variant="error")

                yield Label("[bold]Save/Load[/bold]")
                yield Input(placeholder="filename.txt", id="diagram-filename")
                yield Button("Save", id="btn-diagram-save", variant="success")
                yield Button("Load", id="btn-diagram-load", variant="primary")

                yield Label("[bold]Help[/bold]")
                yield Label("Arrows: Move Cursor\nEnter: Action\nChar: Pen/Text", classes="help-text")

            # Canvas Area
            with Container(id="diagram-canvas-container"):
                yield DiagramCanvas(self.manager, id="diagram-canvas")

    def on_mount(self) -> None:
        self.query_one("#diagram-canvas").focus()

    @on(RadioSet.Changed, "#diagram-tool-select")
    def on_tool_change(self, event: RadioSet.Changed) -> None:
        # Extract tool name from id "tool-name"
        if event.pressed.id:
            self.current_tool = event.pressed.id.replace("tool-", "")
        self.start_pos = None # Reset state
        self.query_one("#diagram-canvas").focus()

    @on(Select.Changed, "#diagram-style-select")
    def on_style_change(self, event: Select.Changed) -> None:
        self.current_style = str(event.value)
        self.query_one("#diagram-canvas").focus()

    @on(Button.Pressed, "#btn-diagram-clear")
    def on_clear(self) -> None:
        self.manager.clear()
        self.query_one("#diagram-canvas").update_content()
        self.query_one("#diagram-canvas").focus()

    @on(Button.Pressed, "#btn-diagram-save")
    def on_save(self) -> None:
        filename = self.query_one("#diagram-filename", Input).value
        if not filename:
            self.notify("Filename required.", severity="error")
            return

        path = self.project_dir / filename
        try:
            self.manager.save(path)
            self.notify(f"Saved to {filename}")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")
        self.query_one("#diagram-canvas").focus()

    @on(Button.Pressed, "#btn-diagram-load")
    def on_load(self) -> None:
        filename = self.query_one("#diagram-filename", Input).value
        if not filename:
            self.notify("Filename required.", severity="error")
            return

        path = self.project_dir / filename
        if not path.exists():
            self.notify("File not found.", severity="error")
            return

        try:
            content = path.read_text(encoding="utf-8")
            self.manager.load(content)
            self.query_one("#diagram-canvas").update_content()
            self.notify(f"Loaded {filename}")
        except Exception as e:
            self.notify(f"Error loading: {e}", severity="error")
        self.query_one("#diagram-canvas").focus()

    # Handle Canvas Input (bubbled up or handled via on_key if focus is correct)
    # Since DiagramCanvas is a custom widget, we can use on_key on the Tab if we ensure focus,
    # OR we can bind on_key in the Canvas. Let's do it in the Canvas and delegate back or handle there.
    # Textual events bubble.

    @on(events.Key)
    def on_key(self, event: events.Key) -> None:
        # Only handle if canvas is focused
        canvas = self.query_one("#diagram-canvas", DiagramCanvas)
        if not canvas.has_focus:
            return

        cx, cy = canvas.cursor_x, canvas.cursor_y

        # Navigation
        if event.key == "up":
            canvas.cursor_y = max(0, cy - 1)
        elif event.key == "down":
            canvas.cursor_y = min(self.manager.height - 1, cy + 1)
        elif event.key == "left":
            canvas.cursor_x = max(0, cx - 1)
        elif event.key == "right":
            canvas.cursor_x = min(self.manager.width - 1, cx + 1)

        # Tools
        elif self.current_tool == "pen" and event.character and len(event.character) == 1:
            self.manager.draw_char(cx, cy, event.character)
            # Auto-advance
            canvas.cursor_x = min(self.manager.width - 1, cx + 1)

        elif self.current_tool == "eraser" and event.key == "space":
            self.manager.draw_char(cx, cy, " ")

        elif event.key == "enter":
            self.handle_tool_action(cx, cy)

        elif self.current_tool == "text" and event.character and len(event.character) == 1:
             # If we are in "text" tool, we might treat it like pen but maybe auto-advance is key
             self.manager.draw_char(cx, cy, event.character)
             canvas.cursor_x = min(self.manager.width - 1, cx + 1)

        canvas.update_content()

    def handle_tool_action(self, x: int, y: int) -> None:
        if self.current_tool in ["line", "box"]:
            if self.start_pos:
                # Finish action
                sx, sy = self.start_pos
                if self.current_tool == "line":
                    self.manager.draw_line(sx, sy, x, y, style=self.current_style)
                    self.notify("Line drawn.")
                elif self.current_tool == "box":
                    self.manager.draw_box(sx, sy, x, y, style=self.current_style)
                    self.notify("Box drawn.")
                self.start_pos = None
            else:
                # Start action
                self.start_pos = (x, y)
                self.notify("Start point set. Move to end and press Enter.")
