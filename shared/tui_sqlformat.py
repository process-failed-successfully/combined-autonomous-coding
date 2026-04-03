import sqlparse
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, TextArea, Select, Checkbox


class TabSqlFormat(Static):
    """A TUI tab for formatting SQL using sqlparse."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("SQL Format Lab", classes="header"),
            Horizontal(
                Static("Keyword Case:", classes="label"),
                Select(
                    options=[("Upper", "upper"), ("Lower", "lower"), ("Capitalize", "capitalize")],
                    value="upper",
                    id="select-keyword-case"
                ),
                Static("Identifier Case:", classes="label"),
                Select(
                    options=[("Lower", "lower"), ("Upper", "upper"), ("Capitalize", "capitalize")],
                    value="lower",
                    id="select-identifier-case"
                ),
                Checkbox("Reindent", value=True, id="checkbox-reindent"),
                classes="controls"
            ),
            TextArea(language="sql", id="input-sql", classes="text-area input-area"),
            Button("Format SQL", id="btn-format", variant="primary"),
            TextArea(language="sql", id="output-sql", classes="text-area output-area", read_only=True),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-format":
            self.format_sql()

    def format_sql(self) -> None:
        input_widget = self.query_one("#input-sql", TextArea)
        output_widget = self.query_one("#output-sql", TextArea)
        keyword_select = self.query_one("#select-keyword-case", Select)
        identifier_select = self.query_one("#select-identifier-case", Select)
        reindent_cb = self.query_one("#checkbox-reindent", Checkbox)

        sql_content = input_widget.text

        if not sql_content.strip():
            output_widget.load_text("")
            return

        try:
            formatted = sqlparse.format(
                sql_content,
                reindent=reindent_cb.value,
                keyword_case=keyword_select.value,
                identifier_case=identifier_select.value
            )
            output_widget.load_text(formatted)
        except Exception as e:
            output_widget.load_text(f"Error formatting SQL:\n{e}")
