import pytest
from unittest.mock import MagicMock
from textual.app import App
from shared.tui_mime import MimeLabTab


# Create a dummy app to avoid full AgentTUI load with Database dependencies
class DummyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notify = MagicMock()


class TestMimeLabTab:
    @pytest.fixture(autouse=True)
    def setup_app(self, tmp_path):
        self.project_dir = tmp_path
        self.app = DummyApp()

    @pytest.mark.asyncio
    async def test_mount(self):
        tab = MimeLabTab(project_dir=self.project_dir)

        async with self.app.run_test() as pilot:
            # Check if tab is reachable/mountable
            await pilot.app.mount(tab)
            assert tab.is_mounted

    @pytest.mark.asyncio
    async def test_lookup_ext(self):
        tab = MimeLabTab(project_dir=self.project_dir)
        async with self.app.run_test() as pilot:
            await pilot.app.mount(tab)
            # Switch to lookup tab
            tab.query_one("TabbedContent").active = "mime-tab-lookup"

            # Input extension
            ext_input = tab.query_one("#mime-ext-input")
            ext_input.value = ".json"

            # Press lookup
            btn = tab.query_one("#btn-mime-lookup-ext")
            btn.press()
            await pilot.pause(0.1)

            # Check result
            lbl = tab.query_one("#mime-lookup-result")
            # In Textual >0.40, use lbl.render() or str(lbl.render())
            assert "application/json" in str(lbl.render())

    @pytest.mark.asyncio
    async def test_lookup_type(self):
        tab = MimeLabTab(project_dir=self.project_dir)
        async with self.app.run_test() as pilot:
            await pilot.app.mount(tab)
            # Switch to lookup tab
            tab.query_one("TabbedContent").active = "mime-tab-lookup"

            # Input mime
            mime_input = tab.query_one("#mime-type-input")
            mime_input.value = "application/json"

            # Press lookup
            btn = tab.query_one("#btn-mime-lookup-type")
            btn.press()
            await pilot.pause(0.1)

            # Check result
            lbl = tab.query_one("#mime-lookup-result")
            assert ".json" in str(lbl.render())

    @pytest.mark.asyncio
    async def test_detect_file(self):
        # Create fake file
        test_file = self.project_dir / "test.png"
        with open(test_file, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n')

        tab = MimeLabTab(project_dir=self.project_dir)
        async with self.app.run_test() as pilot:
            await pilot.app.mount(tab)

            # Setup notification mock
            tab.notify = MagicMock()

            # Input file
            file_input = tab.query_one("#mime-file-input")
            file_input.value = "test.png"

            # Press detect
            btn = tab.query_one("#btn-mime-detect")
            btn.press()
            await pilot.pause(0.1)

            # Check table
            table = tab.query_one("#mime-detect-table")
            row = table.get_row_at(0)  # First row is Best Guess
            # Value is second column (index 1)
            assert "image/png" in str(row[1])

    @pytest.mark.asyncio
    async def test_detect_file_not_found(self):
        tab = MimeLabTab(project_dir=self.project_dir)
        async with self.app.run_test() as pilot:
            await pilot.app.mount(tab)

            # Mock notify
            tab.notify = MagicMock()

            file_input = tab.query_one("#mime-file-input")
            file_input.value = "doesnotexist.txt"

            btn = tab.query_one("#btn-mime-detect")
            btn.press()
            await pilot.pause(0.1)

            tab.notify.assert_called_with("File not found.", severity="error")
