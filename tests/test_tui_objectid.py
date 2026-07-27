import pytest
from textual.app import App
from textual.widgets import Input, RichLog
from shared.tui_objectid import ObjectIdLabTab
from shared.objectid_lab import ObjectIdLabManager

class ObjectIdTestApp(App):
    def compose(self):
        yield ObjectIdLabTab()

@pytest.mark.asyncio
async def test_tui_objectid_generate():
    app = ObjectIdTestApp()
    async with app.run_test() as pilot:
        # Generate is the first tab, so it should be active by default

        # Set count to 2
        count_input = app.query_one("#input-objectid-count", Input)
        count_input.value = "2"

        # Click generate
        await pilot.click("#btn-objectid-generate")
        await pilot.pause(0.2) # Wait for update

        # Check output
        log = app.query_one("#log-objectid-generate", RichLog)
        output_lines = [line.text for line in log.lines]
        output = "".join(output_lines)

        # We should have 2 ObjectIds, so output length should be > 0 and contain 24-char hex strings
        assert len(output) >= 48 # 2 * 24

        # Verify they are valid ObjectIds
        manager = ObjectIdLabManager()
        assert len(output_lines) == 2
        for oid in output_lines:
            assert manager.inspect(oid)["valid"] is True

@pytest.mark.asyncio
async def test_tui_objectid_inspect_valid():
    manager = ObjectIdLabManager()
    oid = manager.generate()[0]

    app = ObjectIdTestApp()
    async with app.run_test() as pilot:
        # Switch to Inspect tab (it's the second tab, ID 'tab-2')
        app.query_one("TabbedContent").active = "tab-2"
        await pilot.pause(0.1)

        # Set objectid
        inspect_input = app.query_one("#input-objectid-inspect", Input)
        inspect_input.value = oid

        # Click inspect
        await pilot.click("#btn-objectid-inspect")
        await pilot.pause(0.2) # Wait for update

        # Check output
        log = app.query_one("#log-objectid-inspect", RichLog)
        output = "".join(line.text for line in log.lines)

        assert "Valid ObjectId" in output
        assert "Generation Time:" in output

@pytest.mark.asyncio
async def test_tui_objectid_inspect_invalid():
    app = ObjectIdTestApp()
    async with app.run_test() as pilot:
        # Switch to Inspect tab
        app.query_one("TabbedContent").active = "tab-2"
        await pilot.pause(0.1)

        # Set invalid objectid
        inspect_input = app.query_one("#input-objectid-inspect", Input)
        inspect_input.value = "invalid_oid_here"

        # Click inspect
        await pilot.click("#btn-objectid-inspect")
        await pilot.pause(0.2) # Wait for update

        # Check output
        log = app.query_one("#log-objectid-inspect", RichLog)
        output = "".join(line.text for line in log.lines)

        assert "Error:" in output
        assert "Invalid ObjectId format" in output
