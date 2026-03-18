import pytest
from unittest.mock import patch
from textual.widgets import TextArea, Button


@pytest.mark.asyncio
async def test_a85_encode():
    from shared.tui_a85 import A85LabTab
    from textual.app import App, ComposeResult
    from typing import Any

    class DummyApp(App[Any]):
        def compose(self) -> ComposeResult:
            yield A85LabTab()

    app = DummyApp()
    async with app.run_test():
        # Get elements
        input_area = app.query_one("#a85-input", TextArea)
        encode_btn = app.query_one("#btn-a85-encode", Button)
        output_area = app.query_one("#a85-output", TextArea)

        # Set input text
        input_area.text = "hello world"

        # Press encode directly on tab
        tab = app.query_one(A85LabTab)
        await tab.on_button_pressed(Button.Pressed(encode_btn))

        # Check output
        # base64.a85encode(b'hello world') = b'BOu!rD]j7BEbo7'
        assert output_area.text == "BOu!rD]j7BEbo7"


@pytest.mark.asyncio
async def test_a85_decode():
    from shared.tui_a85 import A85LabTab
    from textual.app import App, ComposeResult
    from typing import Any

    class DummyApp(App[Any]):
        def compose(self) -> ComposeResult:
            yield A85LabTab()

    app = DummyApp()
    async with app.run_test():
        # Get elements
        input_area = app.query_one("#a85-input", TextArea)
        decode_btn = app.query_one("#btn-a85-decode", Button)
        output_area = app.query_one("#a85-output", TextArea)

        # Set input text
        input_area.text = "BOu!rD]j7BEbo7"

        # Press decode
        tab = app.query_one(A85LabTab)
        await tab.on_button_pressed(Button.Pressed(decode_btn))

        # Check output
        assert output_area.text == "hello world"


@pytest.mark.asyncio
async def test_a85_swap():
    from shared.tui_a85 import A85LabTab
    from textual.app import App, ComposeResult
    from typing import Any

    class DummyApp(App[Any]):
        def compose(self) -> ComposeResult:
            yield A85LabTab()

    app = DummyApp()
    async with app.run_test():
        input_area = app.query_one("#a85-input", TextArea)
        output_area = app.query_one("#a85-output", TextArea)
        swap_btn = app.query_one("#btn-a85-swap", Button)

        input_area.text = "hello"
        output_area.text = "world"

        tab = app.query_one(A85LabTab)
        await tab.on_button_pressed(Button.Pressed(swap_btn))

        assert input_area.text == "world"
        assert output_area.text == "hello"


@pytest.mark.asyncio
async def test_a85_clear():
    from shared.tui_a85 import A85LabTab
    from textual.app import App, ComposeResult
    from typing import Any

    class DummyApp(App[Any]):
        def compose(self) -> ComposeResult:
            yield A85LabTab()

    app = DummyApp()
    async with app.run_test():
        input_area = app.query_one("#a85-input", TextArea)
        output_area = app.query_one("#a85-output", TextArea)
        clear_btn = app.query_one("#btn-a85-clear", Button)

        input_area.text = "hello"
        output_area.text = "world"

        tab = app.query_one(A85LabTab)
        await tab.on_button_pressed(Button.Pressed(clear_btn))

        assert input_area.text == ""
        assert output_area.text == ""


@pytest.mark.asyncio
async def test_a85_empty_input_warning():
    from shared.tui_a85 import A85LabTab
    from textual.app import App, ComposeResult
    from typing import Any

    class DummyApp(App[Any]):
        def compose(self) -> ComposeResult:
            yield A85LabTab()

    app = DummyApp()
    async with app.run_test():
        input_area = app.query_one("#a85-input", TextArea)
        output_area = app.query_one("#a85-output", TextArea)
        encode_btn = app.query_one("#btn-a85-encode", Button)

        # Ensure it's empty
        input_area.text = ""

        tab = app.query_one(A85LabTab)
        with patch.object(tab, 'notify') as mock_notify:
            await tab.on_button_pressed(Button.Pressed(encode_btn))
            mock_notify.assert_called_once_with("Input is empty.", severity="warning")
            assert output_area.text == ""  # Remains empty


@pytest.mark.asyncio
async def test_a85_decode_error():
    from shared.tui_a85 import A85LabTab
    from textual.app import App, ComposeResult
    from typing import Any

    class DummyApp(App[Any]):
        def compose(self) -> ComposeResult:
            yield A85LabTab()

    app = DummyApp()
    async with app.run_test():
        input_area = app.query_one("#a85-input", TextArea)
        output_area = app.query_one("#a85-output", TextArea)
        decode_btn = app.query_one("#btn-a85-decode", Button)

        # Invalid a85 sequence
        input_area.text = "invalid_a85!!!"

        tab = app.query_one(A85LabTab)
        with patch.object(tab, 'notify') as mock_notify:
            await tab.on_button_pressed(Button.Pressed(decode_btn))
            assert "Error:" in output_area.text
            mock_notify.assert_called_once()
            args, kwargs = mock_notify.call_args
            assert "Exception:" in args[0]
            assert kwargs["severity"] == "error"
