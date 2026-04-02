import pytest
from unittest.mock import patch
import io
import argparse

from shared.bip39_lab import Bip39LabManager, run_bip39_lab_logic
import shared.bip39_lab


def test_bip39_lab_manager_init():
    # Test valid initialization
    manager = Bip39LabManager(language="english")
    assert manager.mnemo is not None

    # Test invalid language
    with pytest.raises(ValueError, match="is not supported by the mnemonic library"):
        Bip39LabManager(language="invalid_lang")

    # Test missing library
    with patch.object(shared.bip39_lab, 'Mnemonic', None):
        with pytest.raises(RuntimeError, match="library is not installed"):
            Bip39LabManager()


def test_bip39_lab_manager_generate():
    manager = Bip39LabManager()

    # Valid strength
    res = manager.generate(strength=128)
    assert res["success"] is True
    assert len(res["phrase"].split()) == 12

    res2 = manager.generate(strength=256)
    assert res2["success"] is True
    assert len(res2["phrase"].split()) == 24

    # Invalid strength
    res_invalid = manager.generate(strength=123)
    assert res_invalid["success"] is False
    assert "Invalid strength" in res_invalid["error"]

    # Exception during generation
    with patch.object(manager.mnemo, 'generate', side_effect=Exception("Mocked error")):
        res_ex = manager.generate(strength=128)
        assert res_ex["success"] is False
        assert "Mocked error" in res_ex["error"]


def test_bip39_lab_manager_validate():
    manager = Bip39LabManager()

    # Generate a valid phrase first
    phrase = manager.generate(128)["phrase"]

    res = manager.validate(phrase)
    assert res["success"] is True
    assert res["valid"] is True

    # Invalid phrase
    res_invalid = manager.validate("this is not a valid mnemonic phrase at all")
    assert res_invalid["success"] is True
    assert res_invalid["valid"] is False

    # Exception during validation
    with patch.object(manager.mnemo, 'check', side_effect=Exception("Validation error")):
        res_ex = manager.validate(phrase)
        assert res_ex["success"] is False
        assert "Validation error" in res_ex["error"]


def test_bip39_lab_manager_to_seed():
    manager = Bip39LabManager()
    phrase = manager.generate(128)["phrase"]

    res = manager.to_seed(phrase, passphrase="test")
    assert res["success"] is True
    assert "seed_hex" in res
    assert res["valid_phrase"] is True
    assert len(res["seed_hex"]) == 128  # 64 bytes -> 128 hex chars

    # Exception during seed gen
    with patch.object(manager.mnemo, 'to_seed', side_effect=Exception("Seed error")):
        res_ex = manager.to_seed(phrase)
        assert res_ex["success"] is False
        assert "Seed error" in res_ex["error"]


@patch("sys.stdout", new_callable=io.StringIO)
@patch("sys.stderr", new_callable=io.StringIO)
def test_run_bip39_lab_logic_generate(mock_stderr, mock_stdout):
    args = argparse.Namespace(bip39_action="generate", strength=128, language="english")
    success = run_bip39_lab_logic(args)
    assert success is True
    assert len(mock_stdout.getvalue().strip().split()) == 12

    # Error case
    args_err = argparse.Namespace(bip39_action="generate", strength=999, language="english")
    success = run_bip39_lab_logic(args_err)
    assert success is False
    assert "Error generating mnemonic" in mock_stderr.getvalue()


@patch("sys.stdout", new_callable=io.StringIO)
@patch("sys.stderr", new_callable=io.StringIO)
def test_run_bip39_lab_logic_validate(mock_stderr, mock_stdout):
    manager = Bip39LabManager()
    phrase = manager.generate(128)["phrase"]

    # Valid
    args = argparse.Namespace(bip39_action="validate", phrase=phrase, language="english")
    success = run_bip39_lab_logic(args)
    assert success is True
    assert "VALID" in mock_stdout.getvalue()

    # Invalid
    args_invalid = argparse.Namespace(bip39_action="validate", phrase="invalid phrase", language="english")
    success = run_bip39_lab_logic(args_invalid)
    assert success is False
    assert "INVALID" in mock_stdout.getvalue()

    # Missing phrase
    args_missing = argparse.Namespace(bip39_action="validate", phrase=None, language="english")
    success = run_bip39_lab_logic(args_missing)
    assert success is False
    assert "is required" in mock_stderr.getvalue()


@patch("sys.stdout", new_callable=io.StringIO)
@patch("sys.stderr", new_callable=io.StringIO)
def test_run_bip39_lab_logic_seed(mock_stderr, mock_stdout):
    manager = Bip39LabManager()
    phrase = manager.generate(128)["phrase"]

    # Valid
    args = argparse.Namespace(bip39_action="seed", phrase=phrase, passphrase="", language="english")
    success = run_bip39_lab_logic(args)
    assert success is True
    assert len(mock_stdout.getvalue().strip()) == 128

    # Missing phrase
    args_missing = argparse.Namespace(bip39_action="seed", phrase=None, passphrase="", language="english")
    success = run_bip39_lab_logic(args_missing)
    assert success is False
    assert "is required" in mock_stderr.getvalue()

    # Invalid phrase warning
    args_invalid = argparse.Namespace(bip39_action="seed", phrase="invalid", passphrase="", language="english")
    success = run_bip39_lab_logic(args_invalid)
    assert success is True
    assert "Warning: The provided phrase is invalid" in mock_stderr.getvalue()


@patch("sys.stderr", new_callable=io.StringIO)
def test_run_bip39_lab_logic_errors(mock_stderr):
    # Missing library
    with patch.object(shared.bip39_lab, 'Mnemonic', None):
        args = argparse.Namespace(bip39_action="generate")
        assert run_bip39_lab_logic(args) is False
        assert "library is not installed" in mock_stderr.getvalue()

    # Invalid strength
    mock_stderr.truncate(0)
    mock_stderr.seek(0)
    args = argparse.Namespace(bip39_action="generate", strength=111, language="english")
    assert run_bip39_lab_logic(args) is False
    assert "Invalid strength" in mock_stderr.getvalue()

    # Seed without phrase validation failing but seed succeeds (tested via valid logic),
    # Let's test a failed seed execution
    mock_stderr.truncate(0)
    mock_stderr.seek(0)
    args = argparse.Namespace(bip39_action="seed", phrase="hello", passphrase="", language="english")
    with patch.object(shared.bip39_lab.Bip39LabManager, 'to_seed', return_value={"success": False, "error": "Mocked error"}):
        assert run_bip39_lab_logic(args) is False
        assert "Mocked error" in mock_stderr.getvalue()

    # Validate execution failure
    mock_stderr.truncate(0)
    mock_stderr.seek(0)
    args = argparse.Namespace(bip39_action="validate", phrase="hello", language="english")
    with patch.object(shared.bip39_lab.Bip39LabManager, 'validate', return_value={"success": False, "error": "Mocked val error"}):
        assert run_bip39_lab_logic(args) is False
        assert "Mocked val error" in mock_stderr.getvalue()

    # Missing/invalid subcommand
    mock_stderr.truncate(0)
    mock_stderr.seek(0)
    args_no_sub = argparse.Namespace(bip39_action="unknown", language="english")
    assert run_bip39_lab_logic(args_no_sub) is False
    assert "Invalid or missing subcommand" in mock_stderr.getvalue()

    # Initialization error
    mock_stderr.truncate(0)
    mock_stderr.seek(0)
    args_init_err = argparse.Namespace(bip39_action="generate", language="invalid_lang")
    assert run_bip39_lab_logic(args_init_err) is False
    assert "Error:" in mock_stderr.getvalue()


@pytest.mark.asyncio
async def test_bip39_tui():
    from shared.tui_bip39 import Bip39Tab
    from textual.app import App
    from textual.widgets import Select, Button, TextArea, Input

    class MockApp(App):
        def compose(self):
            yield Bip39Tab()

    app = MockApp()
    async with app.run_test(size=(200, 200)) as pilot:
        tab = app.query_one(Bip39Tab)

        # Initial state is generate
        assert str(tab.mode) == "generate"

        # Change to validate
        select = app.query_one("#bip39-mode-select", Select)
        select.value = "validate"
        await pilot.pause()
        assert str(tab.mode) == "validate"

        # Execute empty validate
        app.query_one("#bip39-btn-execute", Button).press()
        await pilot.pause()
        out = app.query_one("#bip39-output", TextArea).text
        assert "Error: Input phrase is empty" in str(out)

        # Test generate
        select.value = "generate"
        await pilot.pause()
        app.query_one("#bip39-btn-execute", Button).press()
        await pilot.pause()
        generated = app.query_one("#bip39-output", TextArea).text
        assert len(str(generated).split()) == 12

        # Test seed
        select.value = "seed"
        await pilot.pause()
        app.query_one("#bip39-input", TextArea).text = generated
        app.query_one("#bip39-passphrase-input", Input).value = "testpass"
        app.query_one("#bip39-btn-execute", Button).press()
        await pilot.pause()
        seed_out = app.query_one("#bip39-output", TextArea).text
        assert "Seed (Hex):" in str(seed_out)

        # Test invalid phrase seed warning
        app.query_one("#bip39-input", TextArea).text = "invalid words here"
        app.query_one("#bip39-btn-execute", Button).press()
        await pilot.pause()
        seed_out_invalid = app.query_one("#bip39-output", TextArea).text
        assert "WARNING:" in str(seed_out_invalid)

        # Test error handling by breaking the manager temporarily
        with patch.object(tab.manager, 'to_seed', side_effect=Exception("Mock seed error")):
            app.query_one("#bip39-btn-execute", Button).press()
            await pilot.pause()
            err_out = app.query_one("#bip39-output", TextArea).text
            assert "Exception: Mock seed error" in str(err_out)

        select.value = "validate"
        await pilot.pause()
        with patch.object(tab.manager, 'validate', side_effect=Exception("Mock val error")):
            app.query_one("#bip39-btn-execute", Button).press()
            await pilot.pause()
            err_out = app.query_one("#bip39-output", TextArea).text
            assert "Exception: Mock val error" in str(err_out)

        select.value = "generate"
        await pilot.pause()
        with patch.object(tab.manager, 'generate', side_effect=Exception("Mock gen error")):
            app.query_one("#bip39-btn-execute", Button).press()
            await pilot.pause()
            err_out = app.query_one("#bip39-output", TextArea).text
            assert "Exception: Mock gen error" in str(err_out)

        # Test clear
        app.query_one("#bip39-btn-clear", Button).press()
        await pilot.pause()
        assert str(app.query_one("#bip39-input", TextArea).text) == ""
        assert str(app.query_one("#bip39-output", TextArea).text) == ""
        assert str(app.query_one("#bip39-passphrase-input", Input).value) == ""

        # Test valid validate logic
        select.value = "validate"
        await pilot.pause()
        app.query_one("#bip39-input", TextArea).text = generated
        app.query_one("#bip39-btn-execute", Button).press()
        await pilot.pause()
        assert "Valid:" in str(app.query_one("#bip39-output", TextArea).text)

        # Test invalid validate manager return
        with patch.object(tab.manager, 'validate', return_value={"success": False, "error": "Mock fail"}):
            app.query_one("#bip39-btn-execute", Button).press()
            await pilot.pause()
            assert "Error: Mock fail" in str(app.query_one("#bip39-output", TextArea).text)

        # Test invalid generate manager return
        select.value = "generate"
        await pilot.pause()
        with patch.object(tab.manager, 'generate', return_value={"success": False, "error": "Mock fail"}):
            app.query_one("#bip39-btn-execute", Button).press()
            await pilot.pause()
            assert "Error: Mock fail" in str(app.query_one("#bip39-output", TextArea).text)

        # Test invalid seed manager return
        select.value = "seed"
        await pilot.pause()
        app.query_one("#bip39-input", TextArea).text = generated
        with patch.object(tab.manager, 'to_seed', return_value={"success": False, "error": "Mock fail"}):
            app.query_one("#bip39-btn-execute", Button).press()
            await pilot.pause()
            assert "Error: Mock fail" in str(app.query_one("#bip39-output", TextArea).text)

        # Empty seed execution
        app.query_one("#bip39-input", TextArea).text = ""
        app.query_one("#bip39-btn-execute", Button).press()
        await pilot.pause()
        assert "Error: Input phrase is empty." in str(app.query_one("#bip39-output", TextArea).text)

        # Clear exception catching coverage
        # we can't easily delete the input widget so we mock query_one in clear_inputs
        with patch.object(tab, 'query_one', side_effect=Exception("Mocked clear error")):
            tab.clear_inputs()
            await pilot.pause()
            # nothing happens, Exception ignored

        # Execute general exception coverage
        with patch.object(tab, 'query_one', side_effect=Exception("Mocked exec error")):
            tab.execute_operation()
            await pilot.pause()
            # nothing happens, Exception ignored

        # Execute when manager is None
        tab.manager = None
        tab.execute_operation()
        await pilot.pause()

        # Test keybindings
        tab.action_execute()
        await pilot.pause()
        tab.action_clear()
        await pilot.pause()


@pytest.mark.asyncio
async def test_bip39_tui_errors():
    from shared.tui_bip39 import Bip39Tab
    from textual.app import App
    from textual.widgets import Static

    # Test init error
    with patch("shared.tui_bip39.Bip39LabManager", side_effect=Exception("Init Mock Error")):
        class ErrorApp(App):
            def compose(self):
                yield Bip39Tab()

        app = ErrorApp()
        async with app.run_test(size=(200, 200)):
            assert "Error loading BIP39 Lab" in str(app.query_one("#bip39-error", Static).render())
