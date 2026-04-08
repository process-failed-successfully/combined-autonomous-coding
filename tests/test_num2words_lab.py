import pytest
from unittest.mock import patch, MagicMock
from shared.num2words_lab import Num2WordsManager, run_num2words_lab_logic

class TestNum2WordsManager:
    def setup_method(self):
        self.manager = Num2WordsManager()

    def test_convert_zero(self):
        assert self.manager.convert(0) == "zero"

    def test_convert_single_digits(self):
        assert self.manager.convert(5) == "five"
        assert self.manager.convert(9) == "nine"

    def test_convert_teens(self):
        assert self.manager.convert(11) == "eleven"
        assert self.manager.convert(15) == "fifteen"

    def test_convert_tens(self):
        assert self.manager.convert(20) == "twenty"
        assert self.manager.convert(42) == "forty-two"

    def test_convert_hundreds(self):
        assert self.manager.convert(100) == "one hundred"
        assert self.manager.convert(105) == "one hundred five"
        assert self.manager.convert(342) == "three hundred forty-two"

    def test_convert_thousands(self):
        assert self.manager.convert(1000) == "one thousand"
        assert self.manager.convert(1042) == "one thousand forty-two"
        assert self.manager.convert(45015) == "forty-five thousand fifteen"
        assert self.manager.convert(100000) == "one hundred thousand"

    def test_convert_millions(self):
        assert self.manager.convert(1000000) == "one million"
        assert self.manager.convert(2500000) == "two million five hundred thousand"
        assert self.manager.convert(1234567) == "one million two hundred thirty-four thousand five hundred sixty-seven"

    def test_convert_negative(self):
        assert self.manager.convert(-42) == "negative forty-two"
        assert self.manager.convert(-1000) == "negative one thousand"

    def test_convert_string_input(self):
        assert self.manager.convert("123") == "one hundred twenty-three"

    def test_convert_invalid_input(self):
        with pytest.raises(ValueError, match="Input must be a valid integer."):
            self.manager.convert("abc")

    def test_convert_too_large(self):
        with pytest.raises(ValueError, match="Number too large"):
            self.manager.convert(10 ** 21)

class TestNum2WordsLabLogic:
    @patch("builtins.print")
    def test_logic_success(self, mock_print):
        args = MagicMock()
        args.number = "123"
        args.tui = False

        assert run_num2words_lab_logic(args) is True
        mock_print.assert_called_with("one hundred twenty-three")

    @patch("builtins.print")
    def test_logic_error(self, mock_print):
        args = MagicMock()
        args.number = "abc"
        args.tui = False

        assert run_num2words_lab_logic(args) is False
        mock_print.assert_called_with("Error: Input must be a valid integer.")

    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.print")
    def test_logic_no_input(self, mock_print, mock_isatty):
        args = MagicMock()
        args.number = None
        args.tui = False

        assert run_num2words_lab_logic(args) is False
        mock_print.assert_called_with("Error: Number is required for conversion.")

    @patch("sys.stdin.isatty", return_value=False)
    @patch("sys.stdin.read", return_value="456")
    @patch("builtins.print")
    def test_logic_stdin(self, mock_print, mock_read, mock_isatty):
        args = MagicMock()
        args.number = None
        args.tui = False

        assert run_num2words_lab_logic(args) is True
        mock_print.assert_called_with("four hundred fifty-six")

    @patch("main.run_tui")
    @patch("builtins.print")
    def test_logic_tui(self, mock_print, mock_run_tui):
        args = MagicMock()
        args.tui = True

        assert run_num2words_lab_logic(args) is True
        mock_run_tui.assert_called_once()
        mock_print.assert_called_with("Launching Num2Words Lab TUI...")

def test_tui_num2words_lab_import():
    """Test that the TUI component can be imported and instantiated."""
    pytest.importorskip("textual")
    from textual.app import App
    from shared.tui_num2words import TabNum2WordsLab

    class TestApp(App):
        def compose(self):
            yield TabNum2WordsLab()

    app = TestApp()
    assert app is not None

@pytest.mark.asyncio
async def test_tui_num2words_conversion():
    """Test the TUI component conversion logic."""
    pytest.importorskip("textual")
    from textual.app import App
    from textual.widgets import Input, Static
    from shared.tui_num2words import TabNum2WordsLab

    class TestApp(App):
        def compose(self):
            yield TabNum2WordsLab()

    app = TestApp()
    async with app.run_test() as pilot:
        # Get widgets
        input_widget = app.query_one("#num2words-input", Input)
        output_widget = app.query_one("#num2words-output", Static)

        # Test valid input
        input_widget.value = "123"
        await pilot.pause()
        assert "one hundred twenty-three" in str(output_widget.renderable) if hasattr(output_widget, 'renderable') else "one hundred twenty-three" in str(output_widget.render())

        # Test empty input
        input_widget.value = ""
        await pilot.pause()
        assert str(output_widget.renderable) == "" if hasattr(output_widget, 'renderable') else str(output_widget.render()) == ""

        # Test invalid input
        input_widget.value = "abc"
        await pilot.pause()
        assert "Error: Input must be a valid integer." in str(output_widget.renderable) if hasattr(output_widget, 'renderable') else "Error: Input must be a valid integer." in str(output_widget.render())
