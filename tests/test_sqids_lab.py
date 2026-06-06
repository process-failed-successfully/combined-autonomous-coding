import pytest
import argparse
from shared.sqids_lab import SqidsManager, run_sqids_lab_logic

# Import sqids specifically to check if it's available
try:
    from sqids import Sqids
    HAS_SQIDS = True
except ImportError:
    HAS_SQIDS = False

pytestmark = pytest.mark.skipif(not HAS_SQIDS, reason="sqids module not installed")


def test_sqids_encode_decode():
    numbers = [1, 2, 3]
    encoded = SqidsManager.encode(numbers)
    assert isinstance(encoded, str)
    assert len(encoded) > 0

    decoded = SqidsManager.decode(encoded)
    assert decoded == numbers


def test_run_sqids_lab_logic_encode(capsys):
    args = argparse.Namespace(encode="1, 2, 3", decode=None, tui=False)
    success = run_sqids_lab_logic(args)
    assert success is True
    captured = capsys.readouterr()
    encoded = captured.out.strip()
    assert encoded != ""
    assert "Error" not in captured.err


def test_run_sqids_lab_logic_decode(capsys):
    # First encode to get a valid string
    encoded = SqidsManager.encode([1, 2, 3])

    args = argparse.Namespace(encode=None, decode=encoded, tui=False)
    success = run_sqids_lab_logic(args)
    assert success is True
    captured = capsys.readouterr()
    decoded = captured.out.strip()
    assert decoded == "1,2,3"


def test_run_sqids_lab_logic_invalid_encode(capsys):
    args = argparse.Namespace(encode="abc", decode=None, tui=False)
    success = run_sqids_lab_logic(args)
    assert success is False
    captured = capsys.readouterr()
    assert "Sqids Encode Error" in captured.err


def test_run_sqids_lab_logic_invalid_decode(capsys):
    # Decoding a totally invalid string usually yields empty list from sqids
    args = argparse.Namespace(encode=None, decode="!!!", tui=False)
    success = run_sqids_lab_logic(args)
    assert success is False
    captured = capsys.readouterr()
    assert "Sqids Decode Error" in captured.err


def test_run_sqids_lab_logic_no_args(capsys):
    args = argparse.Namespace(encode=None, decode=None, tui=False)
    success = run_sqids_lab_logic(args)
    assert success is False
    captured = capsys.readouterr()
    assert "Error: Must provide either --encode or --decode flag unless using --tui" in captured.err

@pytest.mark.asyncio
async def test_sqids_lab_tui():
    from textual.app import App
    from shared.tui_sqids import SqidsLabTab

    class DummyApp(App):
        def compose(self):
            yield SqidsLabTab()

    app = DummyApp()
    async with app.run_test() as pilot:
        tab = app.query_one(SqidsLabTab)

        # Test Encode
        input_numbers = tab.query_one("#input_numbers")
        input_numbers.value = "4,5,6"

        btn_encode = tab.query_one("#btn_encode")
        await pilot.click("#btn_encode")

        output_encoded = tab.query_one("#output_encoded")
        assert output_encoded.value != ""

        status = tab.query_one("#sqids_status_message")
        assert "Encoded successfully" in str(status.render())

        # Test Decode
        encoded_val = output_encoded.value
        input_sqid = tab.query_one("#input_sqid")
        input_sqid.value = encoded_val

        btn_decode = tab.query_one("#btn_decode")
        await pilot.click("#btn_decode")

        output_decoded = tab.query_one("#output_decoded")
        assert output_decoded.value == "4,5,6"

        assert "Decoded successfully" in str(status.render())
