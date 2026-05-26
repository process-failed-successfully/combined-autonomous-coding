import pytest
from textual.widgets import Input, Select, RichLog
from shared.tui import AgentTUI
from shared.database import init_db
from pathlib import Path

@pytest.mark.asyncio
async def test_tui_enc_lab_base64_encode(tmp_path: Path):
    init_db(tmp_path / ".agent_db.sqlite")
    app = AgentTUI(project_dir=tmp_path, start_tab="tab-enc")

    async with app.run_test() as pilot:
        await pilot.pause()

        # Select base64
        algo_select = app.query_one("#enc-algo-select", Select)
        algo_select.value = "base64"

        # Select encode
        op_select = app.query_one("#enc-op-select", Select)
        op_select.value = "encode"

        # Enter text
        input_widget = app.query_one("#enc-input", Input)
        input_widget.value = "hello world"

        # Directly call the button press handler to avoid UI timing issues
        btn = app.query_one("#btn-enc-process")
        app.query_one("EncLabTab").on_button_pressed(btn.Pressed(btn))
        await pilot.pause()

        log = app.query_one("#enc-log", RichLog)
        text = "\n".join([line.text for line in log.lines])

        assert "aGVsbG8gd29ybGQ=" in text

@pytest.mark.asyncio
async def test_tui_enc_lab_base64_decode(tmp_path: Path):
    init_db(tmp_path / ".agent_db.sqlite")
    app = AgentTUI(project_dir=tmp_path, start_tab="tab-enc")

    async with app.run_test() as pilot:
        await pilot.pause()

        # Select base64
        algo_select = app.query_one("#enc-algo-select", Select)
        algo_select.value = "base64"

        # Select decode
        op_select = app.query_one("#enc-op-select", Select)
        op_select.value = "decode"

        # Enter text
        input_widget = app.query_one("#enc-input", Input)
        input_widget.value = "aGVsbG8gd29ybGQ="

        # Directly call the button press handler
        btn = app.query_one("#btn-enc-process")
        app.query_one("EncLabTab").on_button_pressed(btn.Pressed(btn))
        await pilot.pause()

        log = app.query_one("#enc-log", RichLog)
        text = "\n".join([line.text for line in log.lines])

        assert "hello world" in text

@pytest.mark.asyncio
async def test_tui_enc_lab_hex_encode(tmp_path: Path):
    init_db(tmp_path / ".agent_db.sqlite")
    app = AgentTUI(project_dir=tmp_path, start_tab="tab-enc")

    async with app.run_test() as pilot:
        await pilot.pause()

        # Select hex
        algo_select = app.query_one("#enc-algo-select", Select)
        algo_select.value = "hex"

        # Select encode
        op_select = app.query_one("#enc-op-select", Select)
        op_select.value = "encode"

        # Enter text
        input_widget = app.query_one("#enc-input", Input)
        input_widget.value = "test"

        # Directly call the button press handler
        btn = app.query_one("#btn-enc-process")
        app.query_one("EncLabTab").on_button_pressed(btn.Pressed(btn))
        await pilot.pause()

        log = app.query_one("#enc-log", RichLog)
        text = "\n".join([line.text for line in log.lines])

        assert "74657374" in text

@pytest.mark.asyncio
async def test_tui_enc_lab_clear(tmp_path: Path):
    init_db(tmp_path / ".agent_db.sqlite")
    app = AgentTUI(project_dir=tmp_path, start_tab="tab-enc")

    async with app.run_test() as pilot:
        await pilot.pause()

        # Make a log entry
        input_widget = app.query_one("#enc-input", Input)
        input_widget.value = "test"

        btn_process = app.query_one("#btn-enc-process")
        app.query_one("EncLabTab").on_button_pressed(btn_process.Pressed(btn_process))
        await pilot.pause()

        log = app.query_one("#enc-log", RichLog)
        assert len(log.lines) > 0

        # Clear log
        btn_clear = app.query_one("#btn-enc-clear")
        app.query_one("EncLabTab").on_button_pressed(btn_clear.Pressed(btn_clear))
        await pilot.pause()

        assert len(log.lines) == 0

@pytest.mark.asyncio
async def test_tui_enc_lab_no_input(tmp_path: Path):
    init_db(tmp_path / ".agent_db.sqlite")
    app = AgentTUI(project_dir=tmp_path, start_tab="tab-enc")

    async with app.run_test() as pilot:
        await pilot.pause()

        input_widget = app.query_one("#enc-input", Input)
        input_widget.value = ""

        btn_process = app.query_one("#btn-enc-process")
        app.query_one("EncLabTab").on_button_pressed(btn_process.Pressed(btn_process))
        await pilot.pause()

        log = app.query_one("#enc-log", RichLog)
        text = "\n".join([line.text for line in log.lines])

        assert "Error: Input text required" in text
