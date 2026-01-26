from typing import Iterator
from textual.command import Hit, Provider
from textual.widgets import TabbedContent, TabPane, Button

class NavigationProvider(Provider):
    """Provides navigation commands to switch tabs."""

    async def search(self, query: str) -> Iterator[Hit]:
        matcher = self.matcher(query)

        try:
            tabs_widget = self.app.query_one("#main-tabs", TabbedContent)
        except Exception:
            return

        # Iterate over TabPane children
        for pane in tabs_widget.children:
            if isinstance(pane, TabPane):
                name = pane.title or pane.id
                tab_id = pane.id

                search_text = f"Go to: {name}"
                score = matcher.match(search_text)

                if score > 0:
                    yield Hit(
                        score=score,
                        match_display=matcher.highlight(search_text),
                        command=lambda p=tab_id: self._switch_tab(p),
                        text=search_text,
                        help=f"Switch to {name} tab"
                    )

    def _switch_tab(self, tab_id: str) -> None:
        try:
            tabs = self.app.query_one("#main-tabs", TabbedContent)
            tabs.active = tab_id
        except Exception:
            self.app.notify(f"Could not switch to tab {tab_id}", severity="error")


class ActionProvider(Provider):
    """Provides common global actions."""

    async def search(self, query: str) -> Iterator[Hit]:
        matcher = self.matcher(query)

        actions = [
            ("Run Tests", "btn-test", "Trigger 'Run Tests' button in Dashboard"),
            ("Run Lint", "btn-lint", "Trigger 'Run Lint' button in Dashboard"),
            ("Refresh Dashboard", "btn-refresh", "Refresh Dashboard data"),
            ("Toggle Dark Mode", "toggle_dark", "Toggle application dark mode"),
            ("Quit", "quit", "Exit the application"),
        ]

        for name, key, help_text in actions:
            search_text = f"Global: {name}"
            score = matcher.match(search_text)
            if score > 0:
                yield Hit(
                    score=score,
                    match_display=matcher.highlight(search_text),
                    command=lambda k=key: self._run_action(k),
                    text=search_text,
                    help=help_text
                )

    def _run_action(self, key: str) -> None:
        if key == "toggle_dark":
            self.app.action_toggle_dark()
        elif key == "quit":
            self.app.action_quit()
        else:
            try:
                # These buttons are in the Dashboard tab.
                # If Dashboard is not active, they might still be in the DOM if TabbedContent keeps them mounted.
                # Textual's TabbedContent keeps content mounted but hidden.
                btn = self.app.query_one(f"#{key}", Button)
                btn.press()

                # Also switch to Dashboard tab if we are running a dashboard action
                if key in ["btn-test", "btn-lint", "btn-refresh"]:
                    try:
                        tabs = self.app.query_one("#main-tabs", TabbedContent)
                        if tabs.active != "tab-dashboard":
                            tabs.active = "tab-dashboard"
                    except Exception:
                        pass

            except Exception:
                self.app.notify(f"Action '{key}' not available (widget not found).", severity="warning")
