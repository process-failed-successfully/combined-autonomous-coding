from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Label, Button, DataTable, TabbedContent, TabPane, RichLog, Sparkline
from textual import on
from shared.cq_lab import CodeQualityManager

class CodeQualityTab(Container):
    """Tab for Code Quality Lab."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CodeQualityManager(project_dir)
        self.metrics_cache = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Code Quality Lab[/bold]", classes="welcome-text")

            # Top Score Card
            with Container(classes="stat-box", id="cq-score-card"):
                with Horizontal():
                    yield Label("Grade: [bold]?[/bold]", id="cq-grade-lbl")
                    yield Label("Score: ? / 100", id="cq-score-lbl")
                yield Label("History:", classes="label")
                yield Sparkline(data=[], summary_function="mean", id="cq-history-spark")

            with Horizontal(classes="stat-box"):
                yield Button("Refresh Analysis", id="btn-cq-refresh", variant="primary")
                yield Label("", id="cq-status-lbl")

            with TabbedContent():
                with TabPane("Complexity"):
                    yield DataTable(id="cq-complexity-table")
                with TabPane("Duplication"):
                    yield DataTable(id="cq-duplication-table")
                with TabPane("Security"):
                    yield DataTable(id="cq-security-table")
                with TabPane("Tech Debt"):
                    yield DataTable(id="cq-debt-table")
                with TabPane("Raw Metrics"):
                    yield RichLog(id="cq-raw-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        # Init Tables
        comp_table = self.query_one("#cq-complexity-table", DataTable)
        comp_table.add_columns("Complexity", "Function", "File:Line")

        dup_table = self.query_one("#cq-duplication-table", DataTable)
        dup_table.add_columns("Tokens", "Location 1", "Location 2")

        sec_table = self.query_one("#cq-security-table", DataTable)
        sec_table.add_columns("Severity", "Type", "Description", "File")

        debt_table = self.query_one("#cq-debt-table", DataTable)
        debt_table.add_columns("Type", "File:Line", "Content")

        self.refresh_analysis()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cq-refresh":
            self.refresh_analysis()

    def refresh_analysis(self) -> None:
        self.query_one("#cq-status-lbl").update("Analyzing...")
        self.query_one("#btn-cq-refresh").disabled = True

        import asyncio
        asyncio.create_task(self._run_analysis())

    async def _run_analysis(self) -> None:
        import asyncio
        import json

        try:
            metrics = await asyncio.to_thread(self.manager.collect_metrics)
            result = await asyncio.to_thread(self.manager.calculate_score, metrics)
            await asyncio.to_thread(self.manager.save_history, result)

            self.metrics_cache = {"metrics": metrics, "result": result}
            self._update_ui(metrics, result)

            self.query_one("#cq-status-lbl").update("Analysis complete.")

            # Raw log
            log = self.query_one("#cq-raw-log", RichLog)
            log.clear()
            log.write(json.dumps(result, indent=2))

        except Exception as e:
            self.query_one("#cq-status-lbl").update(f"Error: {e}")
        finally:
            self.query_one("#btn-cq-refresh").disabled = False

    def _update_ui(self, metrics: dict, result: dict) -> None:
        # Score Card
        grade = result["grade"]
        score = result["score"]

        grade_color = "red"
        if grade == "A": grade_color = "green"
        elif grade == "B": grade_color = "cyan"
        elif grade == "C": grade_color = "yellow"
        elif grade == "D": grade_color = "orange"

        self.query_one("#cq-grade-lbl").update(f"Grade: [bold {grade_color}]{grade}[/]")
        self.query_one("#cq-score-lbl").update(f"Score: {score:.1f} / 100")

        # History Sparkline
        history = self.manager.get_history()
        scores = [h["score"] for h in history]
        self.query_one("#cq-history-spark", Sparkline).data = scores

        # Complexity Table
        ct = self.query_one("#cq-complexity-table", DataTable)
        ct.clear()
        for item in metrics["complexity"]["details"]:
            color = "red" if item["complexity"] > 10 else "green"
            ct.add_row(
                f"[{color}]{item['complexity']}[/]",
                item["function"],
                f"{item['file']}:{item['lineno']}"
            )

        # Duplication Table
        dt = self.query_one("#cq-duplication-table", DataTable)
        dt.clear()
        for item in metrics["duplication"]["details"]:
            locs = item["locations"]
            l1 = f"{locs[0]['file']}:{locs[0]['start_line']}"
            l2 = f"{locs[1]['file']}:{locs[1]['start_line']}" if len(locs) > 1 else "N/A"
            dt.add_row(str(item["token_count"]), l1, l2)

        # Security Table
        st = self.query_one("#cq-security-table", DataTable)
        st.clear()
        for item in metrics["security"]["details"]:
            sev = item["severity"]
            s_color = "red" if sev == "HIGH" else "yellow" if sev == "MEDIUM" else "green"
            st.add_row(
                f"[{s_color}]{sev}[/]",
                item["type"],
                item["description"],
                f"{item['file']}:{item['line']}"
            )

        # Debt Table
        dbt = self.query_one("#cq-debt-table", DataTable)
        dbt.clear()
        # TODOs
        for item in metrics["debt"]["details_todos"]:
            dbt.add_row("TODO", f"{item['file']}:{item['line']}", item['content'])
        # Unused
        for item in metrics["debt"]["details_unused"]:
            dbt.add_row("UNUSED", f"{item['file']}:{item['lineno']}", item['name'])
