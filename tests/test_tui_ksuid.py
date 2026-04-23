import pytest

try:
    import textual
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

if TEXTUAL_AVAILABLE:
    from textual.app import App
    from textual.widgets import TabbedContent
    import asyncio
    from shared.tui_ksuid import KsuidLabTab

    class KsuidTestApp(App):
        def compose(self):
            with TabbedContent():
                yield KsuidLabTab()

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="textual is not installed")
@pytest.mark.asyncio
async def test_tui_ksuid_render():
    app = KsuidTestApp()
    async with app.run_test() as pilot:
        assert app.query_one("KsuidLabTab") is not None
        assert app.query_one("#input-ksuid-count") is not None
        assert app.query_one("#btn-ksuid-generate") is not None
        assert app.query_one("#input-ksuid-inspect") is not None
        assert app.query_one("#btn-ksuid-inspect") is not None

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="textual is not installed")
@pytest.mark.asyncio
async def test_tui_ksuid_generate():
    app = KsuidTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(KsuidLabTab)
        tab.action_generate()
        await pilot.pause()
        log = app.query_one("#log-ksuid-generate")
        lines = "".join([line.text for line in log.lines])
        assert len(lines.strip()) == 27

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="textual is not installed")
@pytest.mark.asyncio
async def test_tui_ksuid_inspect_empty():
    app = KsuidTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(KsuidLabTab)
        tab.action_inspect()
        await pilot.pause()
        log = app.query_one("#log-ksuid-inspect")
        output = "".join([line.text for line in log.lines])
        assert "Please enter a KSUID" in output

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="textual is not installed")
@pytest.mark.asyncio
async def test_tui_ksuid_inspect_valid():
    from shared.ksuid_lab import KsuidLabManager
    k = KsuidLabManager().generate()[0]

    app = KsuidTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(KsuidLabTab)
        app.query_one("#input-ksuid-inspect").value = k
        tab.action_inspect()
        await pilot.pause()
        log = app.query_one("#log-ksuid-inspect")
        output = "".join([line.text for line in log.lines])
        assert "Valid KSUID" in output
        assert "Timestamp:" in output
        assert "Payload (Hex):" in output
