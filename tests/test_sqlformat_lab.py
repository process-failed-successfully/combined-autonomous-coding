from unittest.mock import patch
import argparse

from shared.sqlformat_lab import SqlFormatManager, run_sqlformat_lab_logic


def test_sqlformat_manager_format_sql():
    manager = SqlFormatManager()
    sql = "select * from users where id = 1"
    formatted = manager.format_sql(sql)
    assert "SELECT" in formatted
    assert "FROM" in formatted
    assert "WHERE" in formatted
    assert "users" in formatted


def test_sqlformat_manager_process_no_input(capsys):
    manager = SqlFormatManager()
    result = manager.process()
    assert not result
    captured = capsys.readouterr()
    assert "Must provide either input_text or file_path" in captured.err


def test_sqlformat_manager_process_with_text(capsys):
    manager = SqlFormatManager()
    sql = "select id from users"
    result = manager.process(input_text=sql)
    assert result
    captured = capsys.readouterr()
    assert "SELECT" in captured.out
    assert "id" in captured.out


@patch("shared.sqlformat_lab.Path.is_file")
def test_sqlformat_manager_process_with_file_not_found(mock_is_file, capsys):
    mock_is_file.return_value = False
    manager = SqlFormatManager()
    result = manager.process(file_path="dummy.sql")
    assert not result
    captured = capsys.readouterr()
    assert "not found" in captured.err


@patch("shared.sqlformat_lab.Path.is_file")
@patch("shared.sqlformat_lab.Path.read_text")
def test_sqlformat_manager_process_with_file(mock_read_text, mock_is_file, capsys):
    mock_is_file.return_value = True
    mock_read_text.return_value = "select * from test"
    manager = SqlFormatManager()
    result = manager.process(file_path="dummy.sql")
    assert result
    captured = capsys.readouterr()
    assert "SELECT" in captured.out


@patch("shared.sqlformat_lab.Path.is_file")
@patch("shared.sqlformat_lab.Path.read_text")
def test_sqlformat_manager_process_read_error(mock_read_text, mock_is_file, capsys):
    mock_is_file.return_value = True
    mock_read_text.side_effect = Exception("Read error")
    manager = SqlFormatManager()
    result = manager.process(file_path="dummy.sql")
    assert not result
    captured = capsys.readouterr()
    assert "Error reading file" in captured.err


@patch("shared.sqlformat_lab.Path.write_text")
def test_sqlformat_manager_process_with_output(mock_write_text, capsys):
    manager = SqlFormatManager()
    sql = "select 1"
    result = manager.process(input_text=sql, output_path="out.sql")
    assert result
    mock_write_text.assert_called_once()
    captured = capsys.readouterr()
    assert "saved to" in captured.out


@patch("shared.sqlformat_lab.Path.write_text")
def test_sqlformat_manager_process_write_error(mock_write_text, capsys):
    manager = SqlFormatManager()
    mock_write_text.side_effect = Exception("Write error")
    sql = "select 1"
    result = manager.process(input_text=sql, output_path="out.sql")
    assert not result
    captured = capsys.readouterr()
    assert "Error writing to file" in captured.err


@patch("shared.sqlformat_lab.SqlFormatManager.process")
def test_run_sqlformat_lab_logic(mock_process):
    args = argparse.Namespace(
        text="select 1",
        file=None,
        output=None,
        no_reindent=False,
        keyword_case="upper",
        identifier_case="lower"
    )
    mock_process.return_value = True
    result = run_sqlformat_lab_logic(args)
    assert result
    mock_process.assert_called_once_with(
        input_text="select 1",
        file_path=None,
        output_path=None,
        reindent=True,
        keyword_case="upper",
        identifier_case="lower"
    )


def test_run_sqlformat_lab_logic_no_input(capsys):
    args = argparse.Namespace(
        text=None,
        file=None,
        output=None,
        no_reindent=False,
        keyword_case="upper",
        identifier_case="lower"
    )
    result = run_sqlformat_lab_logic(args)
    assert not result
    captured = capsys.readouterr()
    assert "You must provide either --text or --file" in captured.err
