import os
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button, Label, RadioSet, RadioButton, Switch, TextArea
from textual.screen import Screen
from textual.binding import Binding

from shared.set_lab import SetLabManager

class SetLabTab(Vertical):
    """Set Lab TUI Tab"""

    def compose(self) -> ComposeResult:
        with Horizontal(id="set_inputs", classes="p-1"):
            with Vertical(classes="w-1-2 p-1"):
                yield Label("Set 1 (one item per line):")
                yield TextArea(id="set1_input", show_line_numbers=True)
            with Vertical(classes="w-1-2 p-1"):
                yield Label("Set 2 (one item per line):")
                yield TextArea(id="set2_input", show_line_numbers=True)

        with Horizontal(id="set_options", classes="p-1"):
            with Vertical(classes="w-1-2 p-1"):
                yield Label("Operation:")
                with RadioSet(id="operation_radio"):
                    yield RadioButton("Union", id="radio_union", value=True)
                    yield RadioButton("Intersection", id="radio_intersection")
                    yield RadioButton("Difference (Set1 - Set2)", id="radio_difference")
                    yield RadioButton("Symmetric Difference", id="radio_symmetric_difference")
                    yield RadioButton("Is Subset (Set1 ⊆ Set2)", id="radio_subset")
                    yield RadioButton("Is Superset (Set1 ⊇ Set2)", id="radio_superset")

            with Vertical(classes="w-1-2 p-1"):
                yield Label("Options:")
                with Horizontal():
                    yield Label("Ignore Case", classes="p-1")
                    yield Switch(id="ignore_case_switch")
                with Horizontal():
                    yield Label("Trim Whitespace", classes="p-1")
                    yield Switch(id="trim_whitespace_switch", value=True)

                yield Button("Process Sets", id="process_btn", variant="primary", classes="mt-2")

        with Vertical(id="set_output_container", classes="p-1"):
            yield Label("Result:")
            yield TextArea(id="set_result", read_only=True, show_line_numbers=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "process_btn":
            self.process_sets()

    def process_sets(self) -> None:
        set1_text = self.query_one("#set1_input", TextArea).text
        set2_text = self.query_one("#set2_input", TextArea).text

        set1_lines = set1_text.splitlines() if set1_text else []
        set2_lines = set2_text.splitlines() if set2_text else []

        operation_radio = self.query_one("#operation_radio", RadioSet)
        pressed_radio = operation_radio.pressed_button
        if not pressed_radio:
            return

        operation_id = pressed_radio.id
        operation = "union"
        if operation_id == "radio_union":
            operation = "union"
        elif operation_id == "radio_intersection":
            operation = "intersection"
        elif operation_id == "radio_difference":
            operation = "difference"
        elif operation_id == "radio_symmetric_difference":
            operation = "symmetric_difference"
        elif operation_id == "radio_subset":
            operation = "subset"
        elif operation_id == "radio_superset":
            operation = "superset"

        ignore_case = self.query_one("#ignore_case_switch", Switch).value
        trim_whitespace = self.query_one("#trim_whitespace_switch", Switch).value

        manager = SetLabManager()
        result = manager.process_sets(set1_lines, set2_lines, operation, ignore_case, trim_whitespace)

        result_area = self.query_one("#set_result", TextArea)
        if result["success"]:
            if result.get("is_boolean"):
                result_area.text = str(result["result"][0])
            else:
                result_area.text = "\n".join(result["result"])
        else:
            result_area.text = f"Error: {result.get('error')}"
