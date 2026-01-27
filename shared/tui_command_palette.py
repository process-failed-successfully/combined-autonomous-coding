from textual.screen import ModalScreen
from textual.widgets import Input, ListView, ListItem, Label
from textual.containers import Vertical
from textual import on
from textual.app import ComposeResult
from typing import Callable, NamedTuple, Union


class PaletteCommand(NamedTuple):
    title: str
    action: Union[str, Callable]
    id: str = ""


class CommandHit(ListItem):
    def __init__(self, command: PaletteCommand, **kwargs) -> None:
        super().__init__(Label(command.title), **kwargs)
        self.command = command


class AgentCommandPalette(ModalScreen[Union[PaletteCommand, None]]):
    CSS = """
    AgentCommandPalette {
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }

    #palette-container {
        width: 60%;
        height: auto;
        max-height: 50%;
        background: $surface;
        border: solid $accent;
        padding: 1;
    }

    #palette-input {
        margin-bottom: 1;
    }

    #palette-list {
        height: auto;
        max-height: 100%;
    }
    """

    def __init__(self, commands: list[PaletteCommand], **kwargs) -> None:
        super().__init__(**kwargs)
        self.all_commands = commands

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-container"):
            yield Input(placeholder="Type a command...", id="palette-input")
            yield ListView(id="palette-list")

    def on_mount(self) -> None:
        self.update_list(self.all_commands)

    def update_list(self, commands: list[PaletteCommand]) -> None:
        list_view = self.query_one("#palette-list", ListView)
        list_view.clear()

        for cmd in commands:
            list_view.append(CommandHit(cmd))

    @on(Input.Changed, "#palette-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.lower()
        filtered = [
            cmd for cmd in self.all_commands
            if query in cmd.title.lower()
        ]
        self.update_list(filtered)

    @on(Input.Submitted, "#palette-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        list_view = self.query_one("#palette-list", ListView)
        if list_view.children:
            item = list_view.children[0]
            if isinstance(item, CommandHit):
                self.dismiss(item.command)

    @on(ListView.Selected, "#palette-list")
    def on_item_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, CommandHit):
            self.dismiss(item.command)
        else:
            self.dismiss(None)
