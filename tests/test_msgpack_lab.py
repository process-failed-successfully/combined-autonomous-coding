import pytest
from unittest.mock import patch, MagicMock
from shared.msgpack_lab import MsgpackManager, run_msgpack_lab_logic


class TestMsgpackManager:
    def setup_method(self):
        self.manager = MsgpackManager()

    def test_encode_success(self):
        json_str = '{"hello": "world", "num": 42}'
        # 'hello': 'world', 'num': 42 encoded in msgpack then base64
        encoded = self.manager.encode(json_str)
        assert isinstance(encoded, str)
        assert len(encoded) > 0

    def test_encode_invalid_json(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            self.manager.encode('{invalid}')

    def test_decode_success(self):
        # We know base64 of {"test": 123} is "gaR0ZXN0ew=="
        b64 = "gaR0ZXN0ew=="
        decoded = self.manager.decode(b64)
        assert '"test": 123' in decoded

    def test_decode_invalid_b64(self):
        with pytest.raises(ValueError, match="decoding error"):
            self.manager.decode("!!!")


class TestRunMsgpackLabLogic:
    @patch('sys.stdout', new_callable=MagicMock)
    def test_run_encode(self, mock_stdout):
        args = MagicMock()
        args.action = "encode"
        args.data = '{"test": 123}'
        args.tui = False

        result = run_msgpack_lab_logic(args)
        assert result is True
        written = "".join(call[0][0] for call in mock_stdout.write.call_args_list)
        assert "gaR0ZXN0ew==" in written

    @patch('sys.stdout', new_callable=MagicMock)
    def test_run_decode(self, mock_stdout):
        args = MagicMock()
        args.action = "decode"
        args.data = "gaR0ZXN0ew=="
        args.tui = False

        result = run_msgpack_lab_logic(args)
        assert result is True
        written = "".join(call[0][0] for call in mock_stdout.write.call_args_list)
        assert '"test": 123' in written

    @patch('sys.stderr', new_callable=MagicMock)
    def test_run_missing_data(self, mock_stderr):
        args = MagicMock()
        args.action = "encode"
        args.data = None
        args.tui = False

        # If stdin is not a tty, it tries to read.
        # Let's patch sys.stdin.isatty to return True to trigger the error.
        with patch('sys.stdin.isatty', return_value=True):
            result = run_msgpack_lab_logic(args)
            assert result is False
            written = "".join(call[0][0] for call in mock_stderr.write.call_args_list)
            assert "Input data required" in written

    @patch('shared.tui.AgentTUI')
    def test_run_tui(self, mock_tui):
        args = MagicMock()
        args.action = "tui"
        args.project_dir = "test_dir"

        mock_app_instance = MagicMock()
        mock_tui.return_value = mock_app_instance

        with pytest.raises(SystemExit) as e:
            run_msgpack_lab_logic(args)

        assert e.value.code == 0
        mock_tui.assert_called_once_with(project_dir="test_dir", start_tab="tab-msgpack")
        mock_app_instance.run.assert_called_once()
