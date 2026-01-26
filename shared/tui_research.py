from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Input, Button, DataTable, RichLog, Select, Markdown, TabbedContent, TabPane
from textual import on
import asyncio

from shared.research import ResearchManager
from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from shared.knowledge import KnowledgeManager

class ResearchTab(Container):
    """Tab for Autonomous Research."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ResearchManager()
        self.knowledge_manager = KnowledgeManager()
        self.crawled_data = [] # List of dicts {url, content}
        self.selected_url = None
        self.current_summary = ""
        self.research_in_progress = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Research Assistant[/bold]", classes="welcome-text")

            # Configuration
            with Horizontal(classes="stat-box"):
                yield Label("Start URL:")
                yield Input(placeholder="https://example.com/docs", id="research-url")
                yield Label("Depth:")
                yield Input(placeholder="0", id="research-depth", value="0", type="integer")
                yield Label("Limit:")
                yield Input(placeholder="5", id="research-limit", value="5", type="integer")
                yield Button("Start Research", id="btn-research-start", variant="primary")

            with Horizontal():
                # Left Pane: Results List
                with Vertical(id="research-list-container", classes="stat-box"):
                    yield Label("[bold]Visited Pages[/bold]")
                    yield DataTable(id="research-table")
                    yield Label("", id="research-status-lbl")

                # Right Pane: Content & AI
                with Vertical(id="research-content-container"):
                    with Horizontal(classes="stat-box"):
                        yield Label("[bold]Content Preview[/bold]")
                        yield Select.from_values(["gemini", "cursor", "local"], id="research-agent-select", value="gemini")
                        yield Button("Summarize Page", id="btn-research-summarize", variant="warning", disabled=True)
                        yield Button("Save Summary", id="btn-research-save", variant="success", disabled=True)

                    with TabbedContent(id="research-view-tabs"):
                        with TabPane("Content", id="research-tab-content"):
                            yield RichLog(id="research-content-log", wrap=True, highlight=True, markup=False)
                        with TabPane("AI Summary", id="research-tab-summary"):
                            yield Markdown("", id="research-summary-view")

    def on_mount(self) -> None:
        table = self.query_one("#research-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Status", "URL")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-research-start":
            await self.start_research()
        elif event.button.id == "btn-research-summarize":
            await self.summarize_content()
        elif event.button.id == "btn-research-save":
            self.save_summary()

    async def start_research(self) -> None:
        url = self.query_one("#research-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        try:
            depth = int(self.query_one("#research-depth", Input).value)
            limit = int(self.query_one("#research-limit", Input).value)
        except ValueError:
            self.notify("Invalid Depth or Limit.", severity="error")
            return

        self.research_in_progress = True
        self.query_one("#btn-research-start").disabled = True
        self.query_one("#research-status-lbl").update("Researching...")

        table = self.query_one("#research-table", DataTable)
        table.clear()
        self.crawled_data = []

        # Callback to update UI
        def progress_callback(url: str, status: str):
            # We must schedule UI updates on the main thread
            self.app.call_from_thread(self.update_table, url, status)

        try:
            results = await asyncio.to_thread(
                self.manager.crawl,
                url,
                depth=depth,
                limit=limit,
                progress_callback=progress_callback
            )
            self.crawled_data = results
            self.notify(f"Research complete. {len(results)} pages fetched.")
            self.query_one("#research-status-lbl").update(f"Completed. {len(results)} pages.")
        except Exception as e:
            self.notify(f"Research failed: {e}", severity="error")
            self.query_one("#research-status-lbl").update("Failed.")
        finally:
            self.research_in_progress = False
            self.query_one("#btn-research-start").disabled = False

    def update_table(self, url: str, status: str) -> None:
        table = self.query_one("#research-table", DataTable)

        status_display = "[yellow]Fetching...[/yellow]" if status == "fetching" else "[green]Success[/green]"

        if status == "fetching":
            if url not in table.rows:
                table.add_row(status_display, url, key=url)
        else:
            if url in table.rows:
                table.update_cell(url, "Status", status_display)
            else:
                table.add_row(status_display, url, key=url)

    @on(DataTable.RowSelected, "#research-table")
    def on_url_selected(self, event: DataTable.RowSelected) -> None:
        url = event.row_key.value
        self.selected_url = url

        # Find content
        data = next((d for d in self.crawled_data if d["url"] == url), None)
        log = self.query_one("#research-content-log", RichLog)
        log.clear()

        if data:
            log.write(data["content"])
            self.query_one("#btn-research-summarize").disabled = False
        else:
            log.write("Content not available (maybe failed or in progress).")
            self.query_one("#btn-research-summarize").disabled = True

    async def summarize_content(self) -> None:
        if not self.selected_url:
            return

        data = next((d for d in self.crawled_data if d["url"] == self.selected_url), None)
        if not data:
            return

        content = data["content"]
        agent_type = self.query_one("#research-agent-select", Select).value or "gemini"

        self.notify(f"Summarizing with {agent_type}...", severity="information")
        md_view = self.query_one("#research-summary-view", Markdown)
        md_view.update("Generating summary...")

        # Switch to summary tab
        self.query_one("#research-view-tabs", TabbedContent).active = "research-tab-summary"

        try:
            summary = await self.run_agent_summary(content, agent_type)
            self.current_summary = summary
            md_view.update(summary)
            self.query_one("#btn-research-save").disabled = False
            self.notify("Summary generated.")
        except Exception as e:
            md_view.update(f"Error: {e}")
            self.notify(f"Summarization failed: {e}", severity="error")

    async def run_agent_summary(self, content: str, agent_type: str) -> str:
        # Initialize Agent
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            max_iterations=1,
            stream_output=False
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            return "Unknown agent type."

        agent = agent_class(config)

        # Truncate content if too long (approx 20k chars)
        if len(content) > 20000:
            content = content[:20000] + "\n...(truncated)"

        prompt = f"Please summarize the following text. Focus on key technical details and actionable information.\n\nText:\n{content}"

        status, response, actions = await agent.run_agent_session(prompt)
        return response

    def save_summary(self) -> None:
        if not self.selected_url or not self.current_summary:
            return

        try:
            self.knowledge_manager.add_knowledge(
                content=f"Summary of {self.selected_url}:\n\n{self.current_summary}",
                category="RESEARCH_SUMMARY",
                source="tui_research"
            )
            self.notify("Summary saved to Knowledge Base.")
        except Exception as e:
            self.notify(f"Error saving summary: {e}", severity="error")
